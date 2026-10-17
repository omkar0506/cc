from app.models.user import User, CandidateProfile
from app.models.job import JobRole, Skill, JobRoleSkill
from app.models.question import Question
from app.models.interview import InterviewSession, SessionSkillRating, SessionQuestion, Answer
from app.models.evaluation import Evaluation, SkillEvidence
from app.models.learning import LearningItem
from app.models.admin import AppSetting, AuditLog, HumanScore


def test_user_password_hashing():
    """Verify passwords are secure hashes, not stored in plaintext."""
    u = User(email='hash_test@example.com', role='candidate')
    u.set_password('MyStrongPassword123!')
    assert u.password_hash != 'MyStrongPassword123!'
    assert u.check_password('MyStrongPassword123!')
    assert not u.check_password('WrongPassword!')


def test_job_role_and_skills_mapping(db):
    """Verify JobRole, Skill with aliases, and JobRoleSkill relational link."""
    skill = Skill(
        name='Python Test',
        slug='python-test',
        category='technical',
        aliases=['Py', 'Python3']
    )
    db.session.add(skill)
    db.session.flush()

    role = JobRole(
        title='Backend Python Engineer',
        slug='backend-python-engineer',
        description='Build backend microservices with Python and databases.',
        experience_level='Mid-Level',
        interview_topics=['Python Core', 'APIs'],
        difficulty_distribution={'easy': 20, 'medium': 60, 'hard': 20}
    )
    db.session.add(role)
    db.session.flush()

    jrs = JobRoleSkill(
        job_role_id=role.id,
        skill_id=skill.id,
        importance_weight=3.0,
        is_required=True
    )
    db.session.add(jrs)
    db.session.commit()

    assert role.role_skills[0].skill.name == 'Python Test'
    assert role.role_skills[0].importance_weight == 3.0
    assert 'Python3' in role.role_skills[0].skill.aliases


def test_interview_flow_models(db, candidate_user):
    """Verify session, question, answer persistence prior to evaluation."""
    role = JobRole(
        title='QA Role',
        slug='qa-role',
        description='Testing role',
        experience_level='Entry-Level'
    )
    skill = Skill(name='Testing Skill', slug='testing-skill', category='technical')
    db.session.add_all([role, skill])
    db.session.flush()

    session = InterviewSession(
        candidate_id=candidate_user.id,
        job_role_id=role.id,
        category='technical',
        target_difficulty='medium',
        total_questions_limit=5
    )
    db.session.add(session)
    db.session.flush()

    # Pre-interview rating
    rating = SessionSkillRating(
        session_id=session.id,
        skill_id=skill.id,
        rating=4
    )
    db.session.add(rating)

    # Question
    question = Question(
        job_role_id=role.id,
        skill_id=skill.id,
        question_type='technical',
        difficulty='medium',
        question_text='How do you mock dependencies in pytest?',
        expected_concepts=['pytest-mock', 'mocker fixture', 'monkeypatch'],
        reference_answer='Use the mocker fixture to patch objects.',
        rubric={'correctness': 0.5, 'clarity': 0.5},
        max_score=10.0,
        is_approved=True
    )
    db.session.add(question)
    db.session.flush()

    # Session question
    sq = SessionQuestion(
        session_id=session.id,
        question_id=question.id,
        skill_id=skill.id,
        order_index=1,
        difficulty_served='medium',
        adaptive_decision='initial_selection',
        adaptive_reason='First untested required skill'
    )
    db.session.add(sq)
    db.session.flush()

    # Answer saved before evaluation
    ans = Answer(
        session_question_id=sq.id,
        answer_text='We use the mocker fixture or monkeypatch to replace functions with mocks.'
    )
    db.session.add(ans)
    db.session.flush()

    # Evaluation
    eval_rec = Evaluation(
        answer_id=ans.id,
        total_score=8.5,
        max_score=10.0,
        score_ratio=0.85,
        criterion_scores={'correctness': 4.5, 'clarity': 4.0},
        supporting_quotes=['use the mocker fixture or monkeypatch'],
        criterion_explanations={'correctness': 'Accurately identified pytest mock tools.'},
        provider='rule_based'
    )
    db.session.add(eval_rec)

    # Skill Evidence (4 States: Demonstrated, Partially demonstrated, Needs further assessment, Not yet assessed)
    ev = SkillEvidence(
        candidate_id=candidate_user.id,
        session_id=session.id,
        skill_id=skill.id,
        resume_claim=True,
        resume_snippet='Extensive pytest unit testing experience',
        self_rating=4,
        questions_tested_count=1,
        average_score_ratio=0.85,
        status='Partially demonstrated',
        sufficiency_note='Based on 1 evaluated answer at medium difficulty. Another answer needed for full demonstration.'
    )
    db.session.add(ev)
    db.session.commit()

    assert session.session_questions[0].answer.evaluation.total_score == 8.5
    assert ev.status == 'Partially demonstrated'
    assert ev.self_rating == 4


def test_app_setting_helper(db):
    """Test AppSetting get_setting and set_setting helper methods."""
    AppSetting.set_setting('test_key', {'multiplier': 2.5}, 'Test setting')
    val = AppSetting.get_setting('test_key')
    assert val == {'multiplier': 2.5}
    assert AppSetting.get_setting('non_existent_key', default='fallback') == 'fallback'
