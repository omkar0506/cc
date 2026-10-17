import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from app.extensions import db
from app.auth.decorators import admin_required
from app.models.user import User
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question
from app.models.interview import InterviewSession, SessionQuestion
from app.models.admin import AuditLog
from app.admin.forms import JobRoleForm, SkillForm, JobRoleSkillForm, QuestionForm, UserManagementForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Administrator overview dashboard with summary telemetry."""
    users_count = User.query.count()
    candidate_count = User.query.filter_by(role='candidate').count()
    roles_count = JobRole.query.count()
    questions_count = Question.query.count()
    sessions_count = InterviewSession.query.count()
    pending_questions_count = Question.query.filter_by(is_approved=False).count()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        users_count=users_count,
        candidate_count=candidate_count,
        roles_count=roles_count,
        questions_count=questions_count,
        sessions_count=sessions_count,
        pending_questions_count=pending_questions_count,
        recent_logs=recent_logs
    )


# =========================================================================
# USER MANAGEMENT
# =========================================================================

@admin_bp.route('/users')
@admin_required
def users():
    """List and filter system users."""
    role_filter = request.args.get('role', '').strip()
    search_q = request.args.get('q', '').strip()

    query = User.query
    if role_filter in ('candidate', 'admin'):
        query = query.filter_by(role=role_filter)
    if search_q:
        query = query.filter(User.email.ilike(f'%{search_q}%'))

    users_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users_list, role_filter=role_filter, search_q=search_q)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """Edit user role and active status with protection against self-lockout."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    form = UserManagementForm(obj=user)
    if form.validate_on_submit():
        if user.id == current_user.id and not form.is_active.data:
            flash('Security policy: You cannot deactivate your own administrative account.', 'danger')
            return redirect(url_for('admin.user_edit', user_id=user.id))

        old_role = user.role
        old_status = user.is_active
        user.role = form.role.data
        user.is_active = form.is_active.data

        audit = AuditLog(
            user_id=current_user.id,
            action='USER_MODIFIED',
            target_type='users',
            target_id=str(user.id),
            details={
                'email': user.email,
                'role_change': f'{old_role} -> {user.role}',
                'status_change': f'{old_status} -> {user.is_active}'
            },
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash(f'User {user.email} updated successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_edit.html', form=form, user=user)


# =========================================================================
# JOB ROLES MANAGEMENT
# =========================================================================

@admin_bp.route('/roles')
@admin_required
def roles():
    """List all job roles and competency counts."""
    roles_list = JobRole.query.order_by(JobRole.created_at.desc()).all()
    return render_template('admin/roles.html', roles=roles_list)


@admin_bp.route('/roles/new', methods=['GET', 'POST'])
@admin_required
def role_create():
    """Create a new job role."""
    form = JobRoleForm()
    if form.validate_on_submit():
        existing = JobRole.query.filter_by(slug=form.slug.data.strip().lower()).first()
        if existing:
            flash('A job role with this URL slug already exists.', 'danger')
            return render_template('admin/role_edit.html', form=form, is_new=True)

        topics = [t.strip() for t in form.interview_topics_raw.data.split('\n') if t.strip()] if form.interview_topics_raw.data else []
        diff_dist = {
            'easy': form.easy_pct.data or 30,
            'medium': form.medium_pct.data or 50,
            'hard': form.hard_pct.data or 20
        }

        new_role = JobRole(
            title=form.title.data.strip(),
            slug=form.slug.data.strip().lower(),
            description=form.description.data.strip(),
            experience_level=form.experience_level.data,
            interview_topics=topics,
            difficulty_distribution=diff_dist,
            is_active=form.is_active.data
        )
        db.session.add(new_role)
        db.session.flush()

        audit = AuditLog(
            user_id=current_user.id,
            action='JOB_ROLE_CREATED',
            target_type='job_roles',
            target_id=str(new_role.id),
            details={'title': new_role.title, 'slug': new_role.slug},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash(f'Job role "{new_role.title}" created successfully.', 'success')
        return redirect(url_for('admin.role_skills_manage', role_id=new_role.id))

    return render_template('admin/role_edit.html', form=form, is_new=True)


@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@admin_required
def role_edit(role_id):
    """Edit existing job role metadata and difficulty profile."""
    role = db.session.get(JobRole, role_id)
    if not role:
        abort(404)

    form = JobRoleForm(obj=role)
    if request.method == 'GET':
        if role.interview_topics:
            form.interview_topics_raw.data = '\n'.join(role.interview_topics)
        if role.difficulty_distribution:
            form.easy_pct.data = role.difficulty_distribution.get('easy', 30)
            form.medium_pct.data = role.difficulty_distribution.get('medium', 50)
            form.hard_pct.data = role.difficulty_distribution.get('hard', 20)

    if form.validate_on_submit():
        role.title = form.title.data.strip()
        role.slug = form.slug.data.strip().lower()
        role.description = form.description.data.strip()
        role.experience_level = form.experience_level.data
        role.interview_topics = [t.strip() for t in form.interview_topics_raw.data.split('\n') if t.strip()] if form.interview_topics_raw.data else []
        role.difficulty_distribution = {
            'easy': form.easy_pct.data or 30,
            'medium': form.medium_pct.data or 50,
            'hard': form.hard_pct.data or 20
        }
        role.is_active = form.is_active.data

        audit = AuditLog(
            user_id=current_user.id,
            action='JOB_ROLE_UPDATED',
            target_type='job_roles',
            target_id=str(role.id),
            details={'title': role.title},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash(f'Job role "{role.title}" updated successfully.', 'success')
        return redirect(url_for('admin.roles'))

    return render_template('admin/role_edit.html', form=form, role=role, is_new=False)


@admin_bp.route('/roles/<int:role_id>/toggle-status', methods=['POST'])
@admin_required
def role_toggle_status(role_id):
    """Toggle role active or inactive."""
    role = db.session.get(JobRole, role_id)
    if not role:
        abort(404)

    role.is_active = not role.is_active
    audit = AuditLog(
        user_id=current_user.id,
        action='JOB_ROLE_STATUS_TOGGLED',
        target_type='job_roles',
        target_id=str(role.id),
        details={'active': role.is_active},
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Role status changed to {"Active" if role.is_active else "Inactive"}.', 'info')
    return redirect(url_for('admin.roles'))


@admin_bp.route('/roles/<int:role_id>/skills', methods=['GET', 'POST'])
@admin_required
def role_skills_manage(role_id):
    """Manage skills linked to a specific role with weights and requirement flags."""
    role = db.session.get(JobRole, role_id)
    if not role:
        abort(404)

    form = JobRoleSkillForm()
    # Populate skill choices not already linked
    existing_skill_ids = [jrs.skill_id for jrs in role.role_skills]
    available_skills = Skill.query.filter(~Skill.id.in_(existing_skill_ids)).order_by(Skill.name.asc()).all() if existing_skill_ids else Skill.query.order_by(Skill.name.asc()).all()
    form.skill_id.choices = [(s.id, f'{s.name} ({s.category})') for s in available_skills]

    if form.validate_on_submit() and available_skills:
        skill_id = form.skill_id.data
        weight = form.importance_weight.data
        is_req = form.is_required.data

        link = JobRoleSkill(
            job_role_id=role.id,
            skill_id=skill_id,
            importance_weight=weight,
            is_required=is_req
        )
        db.session.add(link)

        audit = AuditLog(
            user_id=current_user.id,
            action='ROLE_SKILL_LINKED',
            target_type='job_role_skills',
            target_id=str(role.id),
            details={'skill_id': skill_id, 'weight': weight, 'required': is_req},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash('Skill competency requirement added successfully.', 'success')
        return redirect(url_for('admin.role_skills_manage', role_id=role.id))

    return render_template('admin/role_skills.html', role=role, form=form, available_skills=available_skills)


@admin_bp.route('/roles/<int:role_id>/skills/<int:skill_id>/remove', methods=['POST'])
@admin_required
def role_skill_remove(role_id, skill_id):
    """Remove a skill requirement from a role."""
    link = JobRoleSkill.query.filter_by(job_role_id=role_id, skill_id=skill_id).first()
    if link:
        db.session.delete(link)
        audit = AuditLog(
            user_id=current_user.id,
            action='ROLE_SKILL_REMOVED',
            target_type='job_role_skills',
            target_id=str(role_id),
            details={'skill_id': skill_id},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        flash('Skill competency removed from role.', 'info')

    return redirect(url_for('admin.role_skills_manage', role_id=role_id))


# =========================================================================
# SKILL REGISTRY MANAGEMENT
# =========================================================================

@admin_bp.route('/skills')
@admin_required
def skills():
    """List all normalized competencies and their aliases."""
    skills_list = Skill.query.order_by(Skill.name.asc()).all()
    return render_template('admin/skills.html', skills=skills_list)


@admin_bp.route('/skills/new', methods=['GET', 'POST'])
@admin_required
def skill_create():
    """Create a new normalized skill."""
    form = SkillForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip().lower()
        if Skill.query.filter_by(slug=slug).first():
            flash('A skill with this URL slug already exists.', 'danger')
            return render_template('admin/skill_edit.html', form=form, is_new=True)

        aliases = [a.strip() for a in form.aliases_raw.data.split(',') if a.strip()] if form.aliases_raw.data else []

        new_skill = Skill(
            name=form.name.data.strip(),
            slug=slug,
            category=form.category.data,
            description=form.description.data.strip() if form.description.data else None,
            aliases=aliases
        )
        db.session.add(new_skill)
        db.session.flush()

        audit = AuditLog(
            user_id=current_user.id,
            action='SKILL_CREATED',
            target_type='skills',
            target_id=str(new_skill.id),
            details={'name': new_skill.name, 'aliases': aliases},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash(f'Skill "{new_skill.name}" added to registry.', 'success')
        return redirect(url_for('admin.skills'))

    return render_template('admin/skill_edit.html', form=form, is_new=True)


@admin_bp.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@admin_required
def skill_edit(skill_id):
    """Edit skill definition and alias mapping."""
    skill = db.session.get(Skill, skill_id)
    if not skill:
        abort(404)

    form = SkillForm(obj=skill)
    if request.method == 'GET' and skill.aliases:
        form.aliases_raw.data = ', '.join(skill.aliases)

    if form.validate_on_submit():
        skill.name = form.name.data.strip()
        skill.slug = form.slug.data.strip().lower()
        skill.category = form.category.data
        skill.description = form.description.data.strip() if form.description.data else None
        skill.aliases = [a.strip() for a in form.aliases_raw.data.split(',') if a.strip()] if form.aliases_raw.data else []

        audit = AuditLog(
            user_id=current_user.id,
            action='SKILL_UPDATED',
            target_type='skills',
            target_id=str(skill.id),
            details={'name': skill.name, 'aliases': skill.aliases},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash(f'Skill "{skill.name}" updated.', 'success')
        return redirect(url_for('admin.skills'))

    return render_template('admin/skill_edit.html', form=form, skill=skill, is_new=False)


# =========================================================================
# QUESTION BANK MANAGEMENT
# =========================================================================

@admin_bp.route('/questions')
@admin_required
def questions():
    """Browse question bank with filters for role, skill, difficulty, and origin."""
    role_id = request.args.get('role_id', type=int)
    skill_id = request.args.get('skill_id', type=int)
    diff = request.args.get('difficulty', '').strip()
    q_type = request.args.get('type', '').strip()
    approved_filter = request.args.get('approved', '').strip()
    search_q = request.args.get('q', '').strip()

    query = Question.query
    if role_id:
        query = query.filter_by(job_role_id=role_id)
    if skill_id:
        query = query.filter_by(skill_id=skill_id)
    if diff in ('easy', 'medium', 'hard'):
        query = query.filter_by(difficulty=diff)
    if q_type in ('technical', 'hr', 'code-written'):
        query = query.filter_by(question_type=q_type)
    if approved_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif approved_filter == 'approved':
        query = query.filter_by(is_approved=True)
    if search_q:
        query = query.filter(Question.question_text.ilike(f'%{search_q}%'))

    questions_list = query.order_by(Question.created_at.desc()).all()
    roles = JobRole.query.order_by(JobRole.title.asc()).all()
    all_skills = Skill.query.order_by(Skill.name.asc()).all()

    return render_template(
        'admin/questions.html',
        questions=questions_list,
        roles=roles,
        skills=all_skills,
        selected_role_id=role_id,
        selected_skill_id=skill_id,
        selected_diff=diff,
        selected_type=q_type,
        selected_approved=approved_filter,
        search_q=search_q
    )


@admin_bp.route('/questions/new', methods=['GET', 'POST'])
@admin_required
def question_create():
    """Add a new vetted question to the question bank."""
    form = QuestionForm()
    roles = JobRole.query.order_by(JobRole.title.asc()).all()
    skills_list = Skill.query.order_by(Skill.name.asc()).all()
    form.job_role_id.choices = [(r.id, r.title) for r in roles]
    form.skill_id.choices = [(s.id, f'{s.name} ({s.category})') for s in skills_list]

    if form.validate_on_submit():
        concepts = [c.strip() for c in form.expected_concepts_raw.data.split('\n') if c.strip()]
        rubric_val = {'correctness': 0.4, 'clarity': 0.3, 'depth': 0.3}
        if form.rubric_raw.data and form.rubric_raw.data.strip():
            try:
                rubric_val = json.loads(form.rubric_raw.data.strip())
            except json.JSONDecodeError:
                pass

        new_q = Question(
            job_role_id=form.job_role_id.data,
            skill_id=form.skill_id.data,
            question_type=form.question_type.data,
            difficulty=form.difficulty.data,
            question_text=form.question_text.data.strip(),
            expected_concepts=concepts,
            reference_answer=form.reference_answer.data.strip(),
            rubric=rubric_val,
            max_score=form.max_score.data,
            is_approved=form.is_approved.data,
            is_active=form.is_active.data,
            origin='admin'
        )
        db.session.add(new_q)
        db.session.flush()

        audit = AuditLog(
            user_id=current_user.id,
            action='QUESTION_CREATED',
            target_type='questions',
            target_id=str(new_q.id),
            details={'role_id': new_q.job_role_id, 'skill_id': new_q.skill_id, 'diff': new_q.difficulty},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash('Question created and registered in bank.', 'success')
        return redirect(url_for('admin.questions'))

    return render_template('admin/question_edit.html', form=form, is_new=True)


@admin_bp.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def question_edit(question_id):
    """Edit question details, rubric, and expected concepts."""
    q = db.session.get(Question, question_id)
    if not q:
        abort(404)

    form = QuestionForm(obj=q)
    roles = JobRole.query.order_by(JobRole.title.asc()).all()
    skills_list = Skill.query.order_by(Skill.name.asc()).all()
    form.job_role_id.choices = [(r.id, r.title) for r in roles]
    form.skill_id.choices = [(s.id, f'{s.name} ({s.category})') for s in skills_list]

    if request.method == 'GET':
        if q.expected_concepts:
            form.expected_concepts_raw.data = '\n'.join(q.expected_concepts)
        if q.rubric:
            form.rubric_raw.data = json.dumps(q.rubric, indent=2)

    if form.validate_on_submit():
        q.job_role_id = form.job_role_id.data
        q.skill_id = form.skill_id.data
        q.question_type = form.question_type.data
        q.difficulty = form.difficulty.data
        q.question_text = form.question_text.data.strip()
        q.expected_concepts = [c.strip() for c in form.expected_concepts_raw.data.split('\n') if c.strip()]
        q.reference_answer = form.reference_answer.data.strip()
        q.max_score = form.max_score.data
        q.is_approved = form.is_approved.data
        q.is_active = form.is_active.data

        if form.rubric_raw.data and form.rubric_raw.data.strip():
            try:
                q.rubric = json.loads(form.rubric_raw.data.strip())
            except json.JSONDecodeError:
                pass

        audit = AuditLog(
            user_id=current_user.id,
            action='QUESTION_UPDATED',
            target_type='questions',
            target_id=str(q.id),
            details={'role_id': q.job_role_id, 'skill_id': q.skill_id},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash('Question updated successfully.', 'success')
        return redirect(url_for('admin.questions'))

    return render_template('admin/question_edit.html', form=form, question=q, is_new=False)


@admin_bp.route('/questions/<int:question_id>/approve', methods=['POST'])
@admin_required
def question_approve(question_id):
    """Approve a pending or AI-generated question."""
    q = db.session.get(Question, question_id)
    if not q:
        abort(404)

    q.is_approved = True
    audit = AuditLog(
        user_id=current_user.id,
        action='QUESTION_APPROVED',
        target_type='questions',
        target_id=str(q.id),
        details={'origin': q.origin},
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Question #{q.id} approved.', 'success')
    return redirect(request.referrer or url_for('admin.questions'))


@admin_bp.route('/questions/<int:question_id>/toggle-status', methods=['POST'])
@admin_required
def question_toggle_status(question_id):
    """Toggle question active/inactive in session candidate question selection."""
    q = db.session.get(Question, question_id)
    if not q:
        abort(404)

    q.is_active = not q.is_active
    audit = AuditLog(
        user_id=current_user.id,
        action='QUESTION_STATUS_TOGGLED',
        target_type='questions',
        target_id=str(q.id),
        details={'active': q.is_active},
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Question #{q.id} is now {"Active" if q.is_active else "Inactive"}.', 'info')
    return redirect(request.referrer or url_for('admin.questions'))
