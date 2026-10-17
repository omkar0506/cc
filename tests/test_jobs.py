from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question


def test_jobs_catalog_view(client, db):
    """Test candidate job roles catalog displays active roles."""
    role1 = JobRole(
        title='DevOps Specialist',
        slug='devops-specialist',
        description='Automate cloud pipelines with Docker and CI/CD.',
        experience_level='Mid-Level',
        is_active=True
    )
    role2 = JobRole(
        title='Archived Role',
        slug='archived-role',
        description='Old inactive role.',
        experience_level='Senior',
        is_active=False
    )
    db.session.add_all([role1, role2])
    db.session.commit()

    res = client.get('/jobs/')
    assert res.status_code == 200
    assert b'DevOps Specialist' in res.data
    # Inactive roles must not be shown to candidates
    assert b'Archived Role' not in res.data


def test_jobs_filter_and_search(client, db):
    """Test searching and filtering job roles by level and keyword."""
    role1 = JobRole(
        title='Golang Microservices Engineer',
        slug='golang-engineer',
        description='High performance concurrency with Go.',
        experience_level='Senior',
        is_active=True
    )
    role2 = JobRole(
        title='Junior Frontend Developer',
        slug='junior-frontend',
        description='React and TypeScript UI development.',
        experience_level='Entry-Level',
        is_active=True
    )
    db.session.add_all([role1, role2])
    db.session.commit()

    # Search keyword
    res_search = client.get('/jobs/?q=Golang')
    assert b'Golang Microservices Engineer' in res_search.data
    assert b'Junior Frontend Developer' not in res_search.data

    # Filter level
    res_level = client.get('/jobs/?level=Entry-Level')
    assert b'Junior Frontend Developer' in res_level.data
    assert b'Golang Microservices Engineer' not in res_level.data


def test_job_role_detail_view(client, db):
    """Test detailed role page with competency matrix and question coverage."""
    role = JobRole(
        title='Machine Learning Engineer',
        slug='ml-engineer',
        description='Build and evaluate predictive machine learning models.',
        experience_level='Mid-Level',
        interview_topics=['Supervised Learning', 'Model Evaluation', 'Feature Engineering'],
        difficulty_distribution={'easy': 25, 'medium': 50, 'hard': 25},
        is_active=True
    )
    skill = Skill(name='Scikit-Learn', slug='scikit-learn', category='technical', aliases=['sklearn'])
    db.session.add_all([role, skill])
    db.session.flush()

    jrs = JobRoleSkill(
        job_role_id=role.id,
        skill_id=skill.id,
        importance_weight=3.5,
        is_required=True
    )
    q = Question(
        job_role_id=role.id,
        skill_id=skill.id,
        question_type='technical',
        difficulty='medium',
        question_text='Explain precision versus recall in classification.',
        expected_concepts=['precision is TP / (TP + FP)', 'recall is TP / (TP + FN)', 'F1 score trade-off'],
        reference_answer='Precision measures accuracy of positive predictions; recall measures coverage of actual positives.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True,
        is_active=True
    )
    db.session.add_all([jrs, q])
    db.session.commit()

    res = client.get('/jobs/ml-engineer')
    assert res.status_code == 200
    assert b'Machine Learning Engineer' in res.data
    assert b'Scikit-Learn' in res.data
    assert b'Required' in res.data
    assert b'3.5' in res.data
    assert b'1 Approved' in res.data


def test_job_role_not_found(client):
    """Test requesting non-existent role slug returns 404."""
    res = client.get('/jobs/non-existent-role')
    assert res.status_code == 404
