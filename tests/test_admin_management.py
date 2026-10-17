from app.extensions import db
from app.models.user import User
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question
from app.models.admin import AuditLog


def test_admin_user_management(client, admin_user, candidate_user):
    """Test administrator can inspect and modify user accounts."""
    # Login as admin
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'AdminSecret123!'})

    # Browse users
    res = client.get('/admin/users')
    assert res.status_code == 200
    assert candidate_user.email.encode() in res.data

    # Edit candidate role to admin
    res_edit = client.post(f'/admin/users/{candidate_user.id}/edit', data={
        'role': 'admin',
        'is_active': 'y'
    }, follow_redirects=True)
    assert res_edit.status_code == 200

    updated_u = db.session.get(User, candidate_user.id)
    assert updated_u.is_admin

    # Self-deactivation prevention check
    res_self = client.post(f'/admin/users/{admin_user.id}/edit', data={
        'role': 'admin'
        # is_active omitted -> False
    }, follow_redirects=True)
    assert b'You cannot deactivate your own administrative account' in res_self.data
    assert db.session.get(User, admin_user.id).is_active is True


def test_admin_job_role_lifecycle(client, admin_user, db):
    """Test administrator can create, edit, toggle, and link competencies to a job role."""
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'AdminSecret123!'})

    # 1. Create a custom role
    res_create = client.post('/admin/roles/new', data={
        'title': 'Site Reliability Engineer',
        'slug': 'site-reliability-engineer',
        'description': 'Maintains high availability and observability across production clusters.',
        'experience_level': 'Mid-Level',
        'interview_topics_raw': 'SRE Fundamentals\nSLIs and SLOs\nChaos Engineering',
        'easy_pct': 20,
        'medium_pct': 50,
        'hard_pct': 30,
        'is_active': 'y'
    }, follow_redirects=True)
    assert res_create.status_code == 200

    new_role = JobRole.query.filter_by(slug='site-reliability-engineer').first()
    assert new_role is not None
    assert new_role.title == 'Site Reliability Engineer'
    assert len(new_role.interview_topics) == 3

    # Verify audit log was recorded
    audit = AuditLog.query.filter_by(action='JOB_ROLE_CREATED', target_id=str(new_role.id)).first()
    assert audit is not None

    # 2. Link a skill to this role
    skill = Skill(name='Kubernetes', slug='kubernetes', category='technical', aliases=['k8s'])
    db.session.add(skill)
    db.session.commit()

    res_link = client.post(f'/admin/roles/{new_role.id}/skills', data={
        'skill_id': skill.id,
        'importance_weight': 3.0,
        'is_required': 'y'
    }, follow_redirects=True)
    assert res_link.status_code == 200
    assert len(new_role.role_skills) == 1
    assert new_role.role_skills[0].skill.name == 'Kubernetes'
    assert new_role.role_skills[0].is_required is True

    # 3. Toggle role status
    client.post(f'/admin/roles/{new_role.id}/toggle-status', follow_redirects=True)
    assert db.session.get(JobRole, new_role.id).is_active is False

    # 4. Remove skill link
    client.post(f'/admin/roles/{new_role.id}/skills/{skill.id}/remove', follow_redirects=True)
    assert len(db.session.get(JobRole, new_role.id).role_skills) == 0


def test_admin_skill_lifecycle(client, admin_user):
    """Test administrator can create and edit normalized competencies with aliases."""
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'AdminSecret123!'})

    # Create new skill
    res = client.post('/admin/skills/new', data={
        'name': 'Redis & In-Memory Caching',
        'slug': 'redis',
        'category': 'technical',
        'description': 'Distributed in-memory key-value storage, caching patterns, pub/sub.',
        'aliases_raw': 'Redis, Key-Value Store, Redis Cache, Memcached'
    }, follow_redirects=True)
    assert res.status_code == 200

    skill = Skill.query.filter_by(slug='redis').first()
    assert skill is not None
    assert 'Redis Cache' in skill.aliases
    assert len(skill.aliases) == 4

    # Edit skill
    client.post(f'/admin/skills/{skill.id}/edit', data={
        'name': 'Redis & Distributed Cache',
        'slug': 'redis',
        'category': 'technical',
        'description': 'Updated description.',
        'aliases_raw': 'Redis, Cache, In-Memory'
    }, follow_redirects=True)

    updated_skill = db.session.get(Skill, skill.id)
    assert updated_skill.name == 'Redis & Distributed Cache'
    assert len(updated_skill.aliases) == 3


def test_admin_question_lifecycle(client, admin_user, db):
    """Test administrator can add, edit, approve, and toggle question status."""
    client.post('/auth/login', data={'email': admin_user.email, 'password': 'AdminSecret123!'})

    role = JobRole(title='Test Role', slug='test-role', description='Desc', is_active=True)
    skill = Skill(name='Test Skill', slug='test-skill', category='technical')
    db.session.add_all([role, skill])
    db.session.commit()

    # Create question
    res_create = client.post('/admin/questions/new', data={
        'job_role_id': role.id,
        'skill_id': skill.id,
        'question_type': 'technical',
        'difficulty': 'medium',
        'question_text': 'Explain the difference between optimistic and pessimistic locking in databases.',
        'expected_concepts_raw': 'optimistic assumes no conflict using version/timestamp\npessimistic locks record using SELECT FOR UPDATE\ntrade-offs in high write contention',
        'reference_answer': 'Optimistic locking checks version fields before commit; pessimistic locking obtains exclusive locks.',
        'rubric_raw': '{"correctness": 0.5, "clarity": 0.5}',
        'max_score': 10.0,
        'is_approved': 'y',
        'is_active': 'y'
    }, follow_redirects=True)
    assert res_create.status_code == 200

    q = Question.query.filter_by(job_role_id=role.id, skill_id=skill.id).first()
    assert q is not None
    assert len(q.expected_concepts) == 3
    assert q.rubric == {'correctness': 0.5, 'clarity': 0.5}
    assert q.is_approved is True

    # Toggle active status
    client.post(f'/admin/questions/{q.id}/toggle-status', follow_redirects=True)
    assert db.session.get(Question, q.id).is_active is False

    # Mark unapproved and then approve via admin button
    q.is_approved = False
    db.session.commit()
    assert db.session.get(Question, q.id).is_approved is False

    client.post(f'/admin/questions/{q.id}/approve', follow_redirects=True)
    assert db.session.get(Question, q.id).is_approved is True
