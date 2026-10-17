"""
Adaptive Question Selection Engine.
Controls persistent session state transitions, follow-up depth caps,
competency prioritization, and difficulty progression according to explicit policies.
"""

from typing import Optional, Tuple, List
from app.extensions import db
from app.models.job import JobRole, JobRoleSkill, Skill
from app.models.question import Question
from app.models.interview import InterviewSession, SessionQuestion
from app.models.evaluation import Evaluation
from app.models.admin import AppSetting


def get_adaptive_policy() -> dict:
    """Load configurable adaptive thresholds and caps from AppSetting or return defaults."""
    default_policy = {
        'high_threshold': 0.80,
        'low_threshold': 0.40,
        'max_followups_per_skill': 2,
        'max_followups_per_question': 1,
        'max_session_questions': 10,
        'min_session_questions': 3
    }
    return AppSetting.get_setting('adaptive_policy', default_policy)


def _get_allowed_types(session: InterviewSession) -> List[str]:
    """Return allowed question types based on session category."""
    if session.category == 'hr':
        return ['hr']
    # Technical interview permits conceptual technical and written code questions
    return ['technical', 'code-written']


def select_initial_question(session: InterviewSession) -> Optional[Tuple[Question, str, str]]:
    """
    Selects the opening question for an interview session:
    Prioritizes the highest-weighted required skill at the starting difficulty.
    """
    allowed_types = _get_allowed_types(session)
    start_diff = session.target_difficulty if session.target_difficulty in ('easy', 'medium', 'hard') else 'medium'

    # Get required skills ordered by importance weight descending
    jrs_list = JobRoleSkill.query.filter_by(
        job_role_id=session.job_role_id,
        is_required=True
    ).order_by(JobRoleSkill.importance_weight.desc()).all()

    # Fallback to optional skills if no required skills
    if not jrs_list:
        jrs_list = JobRoleSkill.query.filter_by(
            job_role_id=session.job_role_id
        ).order_by(JobRoleSkill.importance_weight.desc()).all()

    for jrs in jrs_list:
        q = Question.query.filter(
            Question.job_role_id == session.job_role_id,
            Question.skill_id == jrs.skill_id,
            Question.difficulty == start_diff,
            Question.question_type.in_(allowed_types),
            Question.is_approved == True,
            Question.is_active == True
        ).first()

        if not q:
            # Try any difficulty on this primary skill
            q = Question.query.filter(
                Question.job_role_id == session.job_role_id,
                Question.skill_id == jrs.skill_id,
                Question.question_type.in_(allowed_types),
                Question.is_approved == True,
                Question.is_active == True
            ).first()

        if q:
            decision = 'initial_priority_selection'
            reason = f'Initiated with highest-importance required competency: {jrs.skill.name} (weight {jrs.importance_weight:.1f})'
            return q, decision, reason

    # Fallback across entire question pool for role
    q = Question.query.filter(
        Question.job_role_id == session.job_role_id,
        Question.question_type.in_(allowed_types),
        Question.is_approved == True,
        Question.is_active == True
    ).first()

    if q:
        return q, 'initial_fallback', 'Selected starting question from available approved pool.'
    return None


def select_next_question(
    session: InterviewSession,
    last_sq: SessionQuestion,
    last_eval: Evaluation
) -> Optional[Tuple[Question, str, str, bool, Optional[int]]]:
    """
    Applies the adaptive state machine policy to determine the next question:
    Returns (question, adaptive_decision, adaptive_reason, is_followup, parent_sq_id) or None if session complete.
    """
    asked_sqs = SessionQuestion.query.filter_by(session_id=session.id).all()
    if len(asked_sqs) >= session.total_questions_limit:
        return None

    policy = get_adaptive_policy()
    high_th = policy.get('high_threshold', 0.80)
    low_th = policy.get('low_threshold', 0.40)
    max_skill_followups = policy.get('max_followups_per_skill', 2)
    max_q_followups = policy.get('max_followups_per_question', 1)

    asked_question_ids = {sq.question_id for sq in asked_sqs}
    current_skill_id = last_sq.skill_id
    current_skill = last_sq.skill
    allowed_types = _get_allowed_types(session)

    # Count existing follow-ups on this skill in the session
    skill_followups_count = sum(1 for sq in asked_sqs if sq.skill_id == current_skill_id and sq.is_followup)
    q_followup_count = SessionQuestion.query.filter_by(parent_session_question_id=last_sq.id).count()

    score_ratio = last_eval.score_ratio

    # -------------------------------------------------------------
    # CASE 1: High Score (ratio >= 0.80) -> Deeper challenge or next skill
    # -------------------------------------------------------------
    if score_ratio >= high_th:
        if skill_followups_count < max_skill_followups:
            # Advance difficulty: easy -> medium -> hard
            next_diff = 'medium' if last_sq.difficulty_served == 'easy' else 'hard'
            q = Question.query.filter(
                Question.job_role_id == session.job_role_id,
                Question.skill_id == current_skill_id,
                Question.difficulty == next_diff,
                Question.question_type.in_(allowed_types),
                Question.id.notin_(asked_question_ids),
                Question.is_approved == True,
                Question.is_active == True
            ).first()

            if q:
                decision = 'increase_difficulty'
                reason = f'Score ratio {score_ratio:.2f} >= {high_th:.2f}: advancing from {last_sq.difficulty_served} to {next_diff} on {current_skill.name}'
                return q, decision, reason, True, last_sq.id

        # If already at max difficulty or max depth, transition to next untested skill
        next_cand = _find_next_untested_skill_question(session, asked_sqs, asked_question_ids, preferred_diff='medium')
        if next_cand:
            q, skill_name = next_cand
            decision = 'high_score_next_skill'
            reason = f'Competency on {current_skill.name} verified (ratio {score_ratio:.2f}); transitioning to untested competency {skill_name}.'
            return q, decision, reason, False, None

    # -------------------------------------------------------------
    # CASE 2: Moderate Score (0.40 <= ratio < 0.80) -> Clarifying follow-up
    # -------------------------------------------------------------
    elif low_th <= score_ratio < high_th:
        if q_followup_count < max_q_followups and skill_followups_count < max_skill_followups:
            # Look for another question on this skill at same difficulty
            q = Question.query.filter(
                Question.job_role_id == session.job_role_id,
                Question.skill_id == current_skill_id,
                Question.difficulty == last_sq.difficulty_served,
                Question.question_type.in_(allowed_types),
                Question.id.notin_(asked_question_ids),
                Question.is_approved == True,
                Question.is_active == True
            ).first()

            if q:
                decision = 'clarifying_followup'
                reason = f'Score ratio {score_ratio:.2f} in moderate range ({low_th:.2f}-{high_th:.2f}): clarifying conceptual coverage on {current_skill.name}.'
                return q, decision, reason, True, last_sq.id

        # Otherwise proceed to next priority competency
        next_cand = _find_next_untested_skill_question(session, asked_sqs, asked_question_ids, preferred_diff='medium')
        if next_cand:
            q, skill_name = next_cand
            decision = 'moderate_score_next_skill'
            reason = f'Moving to evaluate breadth across next competency: {skill_name}.'
            return q, decision, reason, False, None

    # -------------------------------------------------------------
    # CASE 3: Low Score (ratio < 0.40) -> Foundational recovery question
    # -------------------------------------------------------------
    else:
        if last_sq.difficulty_served != 'easy' and skill_followups_count < max_skill_followups:
            # Offer one foundational easy question
            q = Question.query.filter(
                Question.job_role_id == session.job_role_id,
                Question.skill_id == current_skill_id,
                Question.difficulty == 'easy',
                Question.question_type.in_(allowed_types),
                Question.id.notin_(asked_question_ids),
                Question.is_approved == True,
                Question.is_active == True
            ).first()

            if q:
                decision = 'foundational_recovery'
                reason = f'Score ratio {score_ratio:.2f} < {low_th:.2f}: providing foundational easy question on {current_skill.name}.'
                return q, decision, reason, True, last_sq.id

        # Switch to next competency to avoid trapping candidate on single topic
        next_cand = _find_next_untested_skill_question(session, asked_sqs, asked_question_ids, preferred_diff='easy')
        if next_cand:
            q, skill_name = next_cand
            decision = 'low_score_switch_skill'
            reason = f'Switched away from {current_skill.name} to {skill_name} to preserve topical breadth.'
            return q, decision, reason, False, None

    # -------------------------------------------------------------
    # FALLBACK: Any unasked approved question for this role
    # -------------------------------------------------------------
    q = Question.query.filter(
        Question.job_role_id == session.job_role_id,
        Question.question_type.in_(allowed_types),
        Question.id.notin_(asked_question_ids),
        Question.is_approved == True,
        Question.is_active == True
    ).first()

    if q:
        decision = 'pool_coverage_fallback'
        reason = f'Broadening coverage with unasked question on {q.skill.name}.'
        return q, decision, reason, False, None

    # No questions remaining in pool
    return None


def _find_next_untested_skill_question(
    session: InterviewSession,
    asked_sqs: List[SessionQuestion],
    asked_question_ids: set,
    preferred_diff: str = 'medium'
) -> Optional[Tuple[Question, str]]:
    """Helper to find an unasked question on the highest-priority untested skill."""
    tested_skill_ids = {sq.skill_id for sq in asked_sqs}
    allowed_types = _get_allowed_types(session)

    # Order required skills by importance weight
    jrs_candidates = JobRoleSkill.query.filter(
        JobRoleSkill.job_role_id == session.job_role_id,
        JobRoleSkill.skill_id.notin_(tested_skill_ids)
    ).order_by(
        JobRoleSkill.is_required.desc(),
        JobRoleSkill.importance_weight.desc()
    ).all()

    for jrs in jrs_candidates:
        q = Question.query.filter(
            Question.job_role_id == session.job_role_id,
            Question.skill_id == jrs.skill_id,
            Question.difficulty == preferred_diff,
            Question.question_type.in_(allowed_types),
            Question.id.notin_(asked_question_ids),
            Question.is_approved == True,
            Question.is_active == True
        ).first()

        if not q:
            # Any difficulty on this untested skill
            q = Question.query.filter(
                Question.job_role_id == session.job_role_id,
                Question.skill_id == jrs.skill_id,
                Question.question_type.in_(allowed_types),
                Question.id.notin_(asked_question_ids),
                Question.is_approved == True,
                Question.is_active == True
            ).first()

        if q:
            return q, jrs.skill.name

    return None
