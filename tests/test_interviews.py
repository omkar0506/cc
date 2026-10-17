from app.extensions import db
from app.models.user import User
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question
from app.models.interview import InterviewSession, SessionSkillRating, SessionQuestion, Answer
from app.models.evaluation import Evaluation
from app.services.evaluator import evaluate_answer_rule_based
from app.services.adaptive_engine import select_initial_question, select_next_question


def setup_interview_environment(db):
    """Helper to set up role, competencies, and multi-difficulty questions."""
    role = JobRole(
        title='Python Backend Engineer',
        slug='python-backend-engineer',
        description='Backend Python development.',
        experience_level='Entry to Mid-Level',
        interview_topics=['Python Core', 'Flask Framework'],
        difficulty_distribution={'easy': 30, 'medium': 50, 'hard': 20},
        is_active=True
    )
    skill_py = Skill(name='Python Core', slug='python-core', category='technical', aliases=['python', 'py'])
    skill_flask = Skill(name='Flask Framework', slug='flask-framework', category='technical', aliases=['flask'])
    db.session.add_all([role, skill_py, skill_flask])
    db.session.flush()

    # Link competencies with weights
    jrs1 = JobRoleSkill(job_role_id=role.id, skill_id=skill_py.id, importance_weight=3.0, is_required=True)
    jrs2 = JobRoleSkill(job_role_id=role.id, skill_id=skill_flask.id, importance_weight=2.0, is_required=True)
    db.session.add_all([jrs1, jrs2])

    # Questions for Python Core
    q_py_easy = Question(
        job_role_id=role.id,
        skill_id=skill_py.id,
        question_type='technical',
        difficulty='easy',
        question_text='What is the difference between list and tuple in Python?',
        expected_concepts=['list is mutable', 'tuple is immutable', 'syntax brackets vs parentheses'],
        reference_answer='Lists are mutable sequences whereas tuples are immutable once created.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True,
        is_active=True
    )
    q_py_med = Question(
        job_role_id=role.id,
        skill_id=skill_py.id,
        question_type='technical',
        difficulty='medium',
        question_text='Explain how generators work with yield in Python.',
        expected_concepts=['yield pauses execution', 'lazy evaluation', 'memory efficient'],
        reference_answer='Generators produce values on demand using yield, avoiding storing entire collections in memory.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True,
        is_active=True
    )
    q_py_hard = Question(
        job_role_id=role.id,
        skill_id=skill_py.id,
        question_type='technical',
        difficulty='hard',
        question_text='Explain the GIL in CPython and memory management.',
        expected_concepts=['Global Interpreter Lock', 'thread safety', 'reference counting', 'cyclic garbage collector'],
        reference_answer='The GIL prevents multiple native threads from executing Python bytecodes concurrently in CPython.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True,
        is_active=True
    )

    # Questions for Flask Framework
    q_flask_med = Question(
        job_role_id=role.id,
        skill_id=skill_flask.id,
        question_type='technical',
        difficulty='medium',
        question_text='What is the application factory pattern in Flask?',
        expected_concepts=['create_app function', 'testing isolation', 'avoids circular imports'],
        reference_answer='The application factory instantiates and configures a Flask app inside a function.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True,
        is_active=True
    )

    db.session.add_all([q_py_easy, q_py_med, q_py_hard, q_flask_med])
    db.session.commit()
    return role, skill_py, skill_flask


def test_rule_based_fallback_evaluator():
    """Verify deterministic concept coverage, quotes extraction, and score boundaries."""
    class MockQuestion:
        expected_concepts = ['mutable list', 'immutable tuple', 'syntax difference']
        rubric = {'correctness': 0.6, 'clarity': 0.4}
        max_score = 10.0

    q = MockQuestion()

    # Good answer
    ans_good = "In Python, a mutable list can be modified in place, whereas an immutable tuple cannot change after creation. There is also a syntax difference using square brackets vs parentheses."
    res_good = evaluate_answer_rule_based(q, ans_good)

    assert res_good['provider'] == 'rule_based'
    assert res_good['total_score'] >= 8.0
    assert res_good['score_ratio'] >= 0.80
    assert len(res_good['supporting_quotes']) > 0
    assert 0.0 <= res_good['total_score'] <= 10.0

    # Poor answer
    ans_poor = "I don't know the exact details about this."
    res_poor = evaluate_answer_rule_based(q, ans_poor)
    assert res_poor['total_score'] < 4.0
    assert len(res_poor['missing_concepts']) >= 2


def test_interview_full_flow(client, candidate_user, db):
    """Test entire interview flow: config -> self-assessment -> answer -> evaluation -> completion."""
    role, skill_py, skill_flask = setup_interview_environment(db)

    # 1. Log in
    client.post('/auth/login', data={'email': candidate_user.email, 'password': 'CandidateSecret123!'})

    # 2. Configure interview
    res_cfg = client.post('/interviews/new', data={
        'job_role_id': role.id,
        'category': 'technical',
        'target_difficulty': 'easy',
        'total_questions_limit': 3,
        'resume_id': 0
    }, follow_redirects=True)
    assert res_cfg.status_code == 200
    assert b'Pre-Interview Skill Self-Assessment' in res_cfg.data

    session = InterviewSession.query.filter_by(candidate_id=candidate_user.id).first()
    assert session is not None
    assert session.status == 'configuring'

    # 3. Submit Self-Assessment ratings
    res_sa = client.post(f'/interviews/{session.session_uuid}/self-assessment', data={
        f'rating_{skill_py.id}': 4,
        f'rating_{skill_flask.id}': 3
    }, follow_redirects=True)
    assert res_sa.status_code == 200
    assert b'Question 1 of 3' in res_sa.data

    # Verify ratings stored
    r1 = SessionSkillRating.query.filter_by(session_id=session.id, skill_id=skill_py.id).first()
    assert r1 is not None and r1.rating == 4

    # Verify session transitioned to in_progress with opening question
    assert session.status == 'in_progress'
    assert len(session.session_questions) == 1
    first_sq = session.session_questions[0]
    assert first_sq.order_index == 1

    # 4. Submit Answer for Question 1
    res_ans1 = client.post(f'/interviews/{session.session_uuid}/session', data={
        'answer_text': 'A list is mutable in Python so you can append elements, while a tuple is immutable and cannot be altered.'
    }, follow_redirects=True)
    assert res_ans1.status_code == 200

    # Verify Answer was saved before evaluation
    db.session.refresh(first_sq)
    assert first_sq.answer is not None
    assert 'list is mutable' in first_sq.answer.answer_text
    assert first_sq.answer.evaluation is not None
    assert first_sq.answer.evaluation.total_score > 0

    # Question 2 served
    assert b'Question 2 of 3' in res_ans1.data
    sq2 = SessionQuestion.query.filter_by(session_id=session.id, order_index=2).first()
    assert sq2 is not None

    # 5. Submit Answer for Question 2
    res_ans2 = client.post(f'/interviews/{session.session_uuid}/session', data={
        'answer_text': 'Generators use yield which pauses execution and provides lazy evaluation so memory usage is low.'
    }, follow_redirects=True)
    assert res_ans2.status_code == 200

    # Question 3 served
    assert b'Question 3 of 3' in res_ans2.data
    sq3 = SessionQuestion.query.filter_by(session_id=session.id, order_index=3).first()
    assert sq3 is not None

    # 6. Submit Answer for Question 3 (reaches limit of 3)
    res_ans3 = client.post(f'/interviews/{session.session_uuid}/session', data={
        'answer_text': 'The create_app function allows application factory pattern to create clean app instances for testing.'
    }, follow_redirects=True)
    assert res_ans3.status_code == 200

    # Session finalized and summary rendered
    db.session.refresh(session)
    assert session.status == 'completed'
    assert session.overall_score is not None
    assert session.completed_at is not None
    assert b'Interview Completed' in res_ans3.data
    assert b'Question-by-Question Evaluation' in res_ans3.data


def test_pause_and_resume_session(client, candidate_user, db):
    """Test candidate can pause an active interview and resume without lost state."""
    role, skill_py, _ = setup_interview_environment(db)
    client.post('/auth/login', data={'email': candidate_user.email, 'password': 'CandidateSecret123!'})

    # Start session
    client.post('/interviews/new', data={
        'job_role_id': role.id,
        'category': 'technical',
        'target_difficulty': 'easy',
        'total_questions_limit': 5,
        'resume_id': 0
    })
    session = InterviewSession.query.filter_by(candidate_id=candidate_user.id).first()
    client.post(f'/interviews/{session.session_uuid}/self-assessment', data={f'rating_{skill_py.id}': 3})

    assert session.status == 'in_progress'

    # Pause session
    res_pause = client.post(f'/interviews/{session.session_uuid}/pause', follow_redirects=True)
    assert res_pause.status_code == 200
    db.session.refresh(session)
    assert session.status == 'paused'

    # Verify appears in history as paused
    res_hist = client.get('/interviews/history')
    assert b'Paused' in res_hist.data

    # Resume session
    res_resume = client.get(f'/interviews/{session.session_uuid}/resume', follow_redirects=True)
    assert res_resume.status_code == 200
    assert b'Question 1 of 5' in res_resume.data
    db.session.refresh(session)
    assert session.status == 'in_progress'


def test_session_data_isolation(client, candidate_user, db):
    """Verify unauthorized users cannot access another candidate's interview session."""
    role, _, _ = setup_interview_environment(db)

    # Candidate 1 creates session
    client.post('/auth/login', data={'email': candidate_user.email, 'password': 'CandidateSecret123!'})
    client.post('/interviews/new', data={
        'job_role_id': role.id,
        'category': 'technical',
        'target_difficulty': 'easy',
        'total_questions_limit': 3,
        'resume_id': 0
    })
    session = InterviewSession.query.filter_by(candidate_id=candidate_user.id).first()
    client.get('/auth/logout')

    # Candidate 2 registers and attempts to access Candidate 1's session
    client.post('/auth/register', data={
        'full_name': 'Hacker Candidate',
        'email': 'attacker@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    client.post('/auth/login', data={'email': 'attacker@example.com', 'password': 'Password123!'})

    # Direct URL access to session should 404
    res_hacked = client.get(f'/interviews/{session.session_uuid}/session')
    assert res_hacked.status_code == 404

    res_hacked_summary = client.get(f'/interviews/{session.session_uuid}/summary')
    assert res_hacked_summary.status_code == 404
