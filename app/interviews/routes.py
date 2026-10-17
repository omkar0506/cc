from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from app.extensions import db
from app.auth.decorators import candidate_required
from app.models.base import utc_now
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.resume import Resume
from app.models.interview import InterviewSession, SessionSkillRating, SessionQuestion, Answer
from app.models.question import Question
from app.models.evaluation import Evaluation
from app.models.admin import AuditLog
from app.interviews.forms import InterviewConfigForm, AnswerSubmissionForm
from app.services.evaluator import evaluate_answer_rule_based
from app.services.adaptive_engine import select_initial_question, select_next_question

interviews_bp = Blueprint('interviews', __name__, url_prefix='/interviews')


@interviews_bp.route('/new', methods=['GET', 'POST'])
@candidate_required
def configure():
    """Step 1: Configure new interview session."""
    form = InterviewConfigForm()

    roles = JobRole.query.filter_by(is_active=True).order_by(JobRole.title.asc()).all()
    form.job_role_id.choices = [(r.id, f'{r.title} ({r.experience_level})') for r in roles]

    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    form.resume_id.choices = [(0, 'None (Standard Assessment)')] + [(r.id, f'{r.original_filename} (Uploaded {r.created_at.strftime("%b %d")})') for r in resumes]

    # Pre-select role if passed in query string (e.g. from job detail page)
    selected_role_slug = request.args.get('role')
    if request.method == 'GET' and selected_role_slug:
        matched_role = JobRole.query.filter_by(slug=selected_role_slug, is_active=True).first()
        if matched_role:
            form.job_role_id.data = matched_role.id

    if form.validate_on_submit():
        role = db.session.get(JobRole, form.job_role_id.data)
        if not role or not role.is_active:
            flash('Selected job role is not active.', 'danger')
            return render_template('interviews/config.html', form=form)

        resume_id_val = form.resume_id.data if form.resume_id.data != 0 else None

        session = InterviewSession(
            candidate_id=current_user.id,
            job_role_id=role.id,
            resume_id=resume_id_val,
            category=form.category.data,
            target_difficulty=form.target_difficulty.data,
            total_questions_limit=form.total_questions_limit.data,
            answer_mode='text',
            status='configuring',
            current_question_index=0
        )
        db.session.add(session)
        db.session.flush()

        audit = AuditLog(
            user_id=current_user.id,
            action='INTERVIEW_SESSION_CREATED',
            target_type='interview_sessions',
            target_id=str(session.id),
            details={'role': role.title, 'category': session.category, 'limit': session.total_questions_limit},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        return redirect(url_for('interviews.self_assessment', session_uuid=session.session_uuid))

    return render_template('interviews/config.html', form=form)


@interviews_bp.route('/<session_uuid>/self-assessment', methods=['GET', 'POST'])
@candidate_required
def self_assessment(session_uuid):
    """Step 2: Pre-interview confidence self-assessment for target skills (1 to 5)."""
    session = InterviewSession.query.filter_by(session_uuid=session_uuid).first()
    if not session or session.candidate_id != current_user.id:
        abort(404)

    if session.status != 'configuring':
        # If already configured, jump to session
        return redirect(url_for('interviews.live_session', session_uuid=session.session_uuid))

    role = session.job_role
    skills = [jrs.skill for jrs in role.role_skills]

    if request.method == 'POST':
        ratings_saved = 0
        for skill in skills:
            field_name = f'rating_{skill.id}'
            rating_val = request.form.get(field_name, type=int)
            if rating_val and 1 <= rating_val <= 5:
                # Upsert rating
                existing_r = SessionSkillRating.query.filter_by(session_id=session.id, skill_id=skill.id).first()
                if not existing_r:
                    sr = SessionSkillRating(session_id=session.id, skill_id=skill.id, rating=rating_val)
                    db.session.add(sr)
                else:
                    existing_r.rating = rating_val
                ratings_saved += 1

        # Select initial question
        initial_pick = select_initial_question(session)
        if not initial_pick:
            flash('Error: No approved questions available in question bank for this role.', 'danger')
            return redirect(url_for('interviews.configure'))

        first_q, decision, reason = initial_pick
        sq = SessionQuestion(
            session_id=session.id,
            question_id=first_q.id,
            skill_id=first_q.skill_id,
            order_index=1,
            difficulty_served=first_q.difficulty,
            is_followup=False,
            adaptive_decision=decision,
            adaptive_reason=reason
        )
        db.session.add(sq)

        session.status = 'in_progress'
        session.started_at = utc_now()
        session.current_question_index = 1
        db.session.commit()

        flash('Confidence ratings saved. Your practice interview has begun!', 'success')
        return redirect(url_for('interviews.live_session', session_uuid=session.session_uuid))

    return render_template('interviews/self_assessment.html', session=session, skills=skills, role=role)


@interviews_bp.route('/<session_uuid>/session', methods=['GET', 'POST'])
@candidate_required
def live_session(session_uuid):
    """Step 3: Live interview question presentation and answer submission."""
    session = InterviewSession.query.filter_by(session_uuid=session_uuid).first()
    if not session or session.candidate_id != current_user.id:
        abort(404)

    if session.status == 'completed':
        return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))

    if session.status == 'paused':
        # Automatically resume if candidate opens the live URL
        session.status = 'in_progress'
        db.session.commit()

    # Find the current active question (where answer is None)
    active_sq = SessionQuestion.query.filter_by(
        session_id=session.id
    ).outerjoin(Answer).filter(Answer.id == None).first()

    # If no active question without an answer exists, check if session limit reached or pick next
    if not active_sq:
        completed_count = SessionQuestion.query.filter_by(session_id=session.id).join(Answer).count()
        if completed_count >= session.total_questions_limit:
            _finalize_session(session)
            return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))

        # Check last answered question to trigger adaptive transition
        last_answered_sq = SessionQuestion.query.filter_by(
            session_id=session.id
        ).join(Answer).order_by(SessionQuestion.order_index.desc()).first()

        if last_answered_sq and last_answered_sq.answer and last_answered_sq.answer.evaluation:
            next_pick = select_next_question(session, last_answered_sq, last_answered_sq.answer.evaluation)
            if next_pick:
                next_q, decision, reason, is_followup, parent_id = next_pick
                next_order = last_answered_sq.order_index + 1
                active_sq = SessionQuestion(
                    session_id=session.id,
                    question_id=next_q.id,
                    skill_id=next_q.skill_id,
                    order_index=next_order,
                    difficulty_served=next_q.difficulty,
                    parent_session_question_id=parent_id,
                    is_followup=is_followup,
                    adaptive_decision=decision,
                    adaptive_reason=reason
                )
                db.session.add(active_sq)
                session.current_question_index = next_order
                db.session.commit()
            else:
                _finalize_session(session)
                return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))
        else:
            _finalize_session(session)
            return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))

    form = AnswerSubmissionForm()

    if form.validate_on_submit():
        answer_text = form.answer_text.data.strip()

        # Step 1: Save Answer to MySQL BEFORE evaluation (zero data loss guarantee)
        answer = Answer(
            session_question_id=active_sq.id,
            answer_text=answer_text,
            submitted_at=utc_now()
        )
        db.session.add(answer)
        db.session.flush()

        # Step 2: Evaluate answer against rubric using concept-coverage fallback
        eval_result = evaluate_answer_rule_based(active_sq.question, answer_text)

        # Step 3: Persist evaluation to MySQL
        evaluation = Evaluation(
            answer_id=answer.id,
            total_score=eval_result['total_score'],
            max_score=eval_result['max_score'],
            score_ratio=eval_result['score_ratio'],
            criterion_scores=eval_result['criterion_scores'],
            supporting_quotes=eval_result['supporting_quotes'],
            criterion_explanations=eval_result['criterion_explanations'],
            missing_concepts=eval_result['missing_concepts'],
            strengths=eval_result['strengths'],
            improvement_suggestions=eval_result['improvement_suggestions'],
            suggested_followup=eval_result['suggested_followup'],
            provider=eval_result['provider'],
            model=eval_result['model'],
            tokens_used=eval_result['tokens_used'],
            status='completed',
            evaluated_at=utc_now()
        )
        db.session.add(evaluation)
        db.session.flush()

        # Check if interview reached question cap
        total_answered = SessionQuestion.query.filter_by(session_id=session.id).join(Answer).count()

        if total_answered >= session.total_questions_limit:
            _finalize_session(session)
            db.session.commit()
            flash('Interview session completed! Review your feedback below.', 'success')
            return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))

        # Select next question via adaptive engine
        next_pick = select_next_question(session, active_sq, evaluation)
        if next_pick:
            next_q, decision, reason, is_followup, parent_id = next_pick
            next_order = active_sq.order_index + 1
            next_sq = SessionQuestion(
                session_id=session.id,
                question_id=next_q.id,
                skill_id=next_q.skill_id,
                order_index=next_order,
                difficulty_served=next_q.difficulty,
                parent_session_question_id=parent_id,
                is_followup=is_followup,
                adaptive_decision=decision,
                adaptive_reason=reason
            )
            db.session.add(next_sq)
            session.current_question_index = next_order
            db.session.commit()

            return redirect(url_for('interviews.live_session', session_uuid=session.session_uuid))
        else:
            _finalize_session(session)
            db.session.commit()
            flash('Question pool exhausted. Session successfully concluded.', 'info')
            return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))

    return render_template(
        'interviews/session.html',
        session=session,
        active_sq=active_sq,
        question=active_sq.question,
        form=form
    )


@interviews_bp.route('/<session_uuid>/pause', methods=['POST'])
@candidate_required
def pause_session(session_uuid):
    """Pause an active session; allows resume anytime without losing progress."""
    session = InterviewSession.query.filter_by(session_uuid=session_uuid).first()
    if not session or session.candidate_id != current_user.id:
        abort(404)

    if session.status == 'in_progress':
        session.status = 'paused'
        db.session.commit()
        flash('Interview paused. You can resume this session anytime from your history.', 'info')

    return redirect(url_for('interviews.history'))


@interviews_bp.route('/<session_uuid>/resume')
@candidate_required
def resume_session(session_uuid):
    """Resume an interrupted or paused session from the exact saved state."""
    session = InterviewSession.query.filter_by(session_uuid=session_uuid).first()
    if not session or session.candidate_id != current_user.id:
        abort(404)

    if session.status in ('paused', 'in_progress'):
        session.status = 'in_progress'
        db.session.commit()
        return redirect(url_for('interviews.live_session', session_uuid=session.session_uuid))

    return redirect(url_for('interviews.summary', session_uuid=session.session_uuid))


@interviews_bp.route('/history')
@candidate_required
def history():
    """List all interview attempts with status, scores, and resume links."""
    sessions = InterviewSession.query.filter_by(
        candidate_id=current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()

    return render_template('interviews/history.html', sessions=sessions)


@interviews_bp.route('/<session_uuid>/summary')
@candidate_required
def summary(session_uuid):
    """Preliminary session summary displaying feedback, scores, and adaptive decision trail."""
    session = InterviewSession.query.filter_by(session_uuid=session_uuid).first()
    if not session or session.candidate_id != current_user.id:
        abort(404)

    sq_list = SessionQuestion.query.filter_by(
        session_id=session.id
    ).order_by(SessionQuestion.order_index.asc()).all()

    return render_template('interviews/summary.html', session=session, sq_list=sq_list)


def _finalize_session(session: InterviewSession):
    """Calculates overall score, updates session status to completed and records completion timestamp."""
    session.status = 'completed'
    session.completed_at = utc_now()

    # Aggregate scores from all evaluated answers
    evals = Evaluation.query.join(Answer).join(SessionQuestion).filter(
        SessionQuestion.session_id == session.id
    ).all()

    if evals:
        total_score_sum = sum(e.total_score for e in evals)
        avg_score = total_score_sum / len(evals)
        session.overall_score = round(avg_score, 2)
        session.max_possible_score = 10.0
        session.scoring_summary = {
            'evaluated_answers_count': len(evals),
            'total_score_sum': round(total_score_sum, 2),
            'average_score': round(avg_score, 2),
            'score_ratio': round(avg_score / 10.0, 4)
        }
    else:
        session.overall_score = 0.0
        session.max_possible_score = 10.0
