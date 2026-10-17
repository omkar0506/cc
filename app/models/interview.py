import uuid
from app.extensions import db
from app.models.base import utc_now


class InterviewSession(db.Model):
    """Interview session tracking configuration, state machine progress, and scores."""
    __tablename__ = 'interview_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_uuid = db.Column(db.String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_roles.id', ondelete='RESTRICT'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True)
    category = db.Column(db.String(30), default='technical', nullable=False)  # 'technical', 'hr'
    target_difficulty = db.Column(db.String(20), default='medium', nullable=False)  # 'easy', 'medium', 'hard', 'adaptive'
    total_questions_limit = db.Column(db.Integer, default=5, nullable=False)  # 3 to 10
    answer_mode = db.Column(db.String(20), default='text', nullable=False)
    status = db.Column(db.String(30), default='configuring', nullable=False)  # 'configuring', 'in_progress', 'completed', 'paused', 'abandoned'
    current_question_index = db.Column(db.Integer, default=0, nullable=False)
    overall_score = db.Column(db.Float, nullable=True)
    max_possible_score = db.Column(db.Float, nullable=True)
    scoring_summary = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    candidate = db.relationship('User', back_populates='interview_sessions')
    job_role = db.relationship('JobRole', back_populates='interview_sessions')
    resume = db.relationship('Resume', back_populates='interview_sessions')
    skill_ratings = db.relationship(
        'SessionSkillRating',
        back_populates='session',
        cascade='all, delete-orphan'
    )
    session_questions = db.relationship(
        'SessionQuestion',
        back_populates='session',
        cascade='all, delete-orphan',
        order_by='SessionQuestion.order_index.asc()'
    )
    skill_evidence = db.relationship(
        'SkillEvidence',
        back_populates='session',
        cascade='all, delete-orphan'
    )
    learning_items = db.relationship(
        'LearningItem',
        back_populates='session',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<InterviewSession {self.session_uuid} user={self.candidate_id} status={self.status}>'


class SessionSkillRating(db.Model):
    """Candidate pre-interview confidence self-assessment for target skills (1 to 5)."""
    __tablename__ = 'session_skill_ratings'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'skill_id', name='uq_session_skill_rating'),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 (new) to 5 (very confident)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    session = db.relationship('InterviewSession', back_populates='skill_ratings')
    skill = db.relationship('Skill')

    def __repr__(self):
        return f'<SessionSkillRating session={self.session_id} skill={self.skill_id} rating={self.rating}>'


class SessionQuestion(db.Model):
    """Questions served in a session with sequence, difficulty, parent linkage, and adaptive audit."""
    __tablename__ = 'session_questions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='RESTRICT'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    difficulty_served = db.Column(db.String(20), nullable=False)
    parent_session_question_id = db.Column(db.Integer, db.ForeignKey('session_questions.id', ondelete='SET NULL'), nullable=True)
    is_followup = db.Column(db.Boolean, default=False, nullable=False)
    adaptive_decision = db.Column(db.String(100), nullable=True)  # e.g., 'increase_difficulty', 'clarifying_followup', 'foundational_switch'
    adaptive_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    session = db.relationship('InterviewSession', back_populates='session_questions')
    question = db.relationship('Question', back_populates='session_questions')
    skill = db.relationship('Skill')
    parent = db.relationship('SessionQuestion', remote_side=[id], backref=db.backref('followups', lazy='dynamic'))
    answer = db.relationship('Answer', back_populates='session_question', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SessionQuestion {self.id}: session={self.session_id} q={self.question_id} order={self.order_index}>'


class Answer(db.Model):
    """Candidate response persisted prior to evaluation to guarantee zero data loss."""
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    session_question_id = db.Column(db.Integer, db.ForeignKey('session_questions.id', ondelete='CASCADE'), unique=True, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    session_question = db.relationship('SessionQuestion', back_populates='answer')
    evaluation = db.relationship('Evaluation', back_populates='answer', uselist=False, cascade='all, delete-orphan')
    human_scores = db.relationship('HumanScore', back_populates='answer', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Answer {self.id} for session_question={self.session_question_id}>'
