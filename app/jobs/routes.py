from flask import Blueprint, render_template, abort, request
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')


@jobs_bp.route('/')
def index():
    """Browse all active job roles with search and level filters."""
    query = JobRole.query.filter_by(is_active=True)

    level_filter = request.args.get('level', '').strip()
    if level_filter:
        query = query.filter(JobRole.experience_level.ilike(f'%{level_filter}%'))

    search_kw = request.args.get('q', '').strip()
    if search_kw:
        query = query.filter(
            (JobRole.title.ilike(f'%{search_kw}%')) |
            (JobRole.description.ilike(f'%{search_kw}%'))
        )

    roles = query.order_by(JobRole.title.asc()).all()
    all_levels = ['Entry-Level', 'Entry to Mid-Level', 'Mid-Level', 'Senior']

    return render_template(
        'jobs/index.html',
        roles=roles,
        all_levels=all_levels,
        selected_level=level_filter,
        search_kw=search_kw
    )


@jobs_bp.route('/<slug>')
def detail(slug):
    """Detailed job role specification with competency matrix and question coverage."""
    role = JobRole.query.filter_by(slug=slug, is_active=True).first()
    if not role:
        abort(404)

    # Build competency matrix with question counts
    matrix = []
    for jrs in role.role_skills:
        q_count = Question.query.filter_by(
            job_role_id=role.id,
            skill_id=jrs.skill_id,
            is_approved=True,
            is_active=True
        ).count()
        matrix.append({
            'skill': jrs.skill,
            'importance_weight': jrs.importance_weight,
            'is_required': jrs.is_required,
            'approved_questions_count': q_count
        })

    # Sort required first, then by importance weight descending
    matrix.sort(key=lambda x: (x['is_required'], x['importance_weight']), reverse=True)

    return render_template('jobs/detail.html', role=role, matrix=matrix)
