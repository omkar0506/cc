from app.extensions import db
from app.models.base import utc_now


class Question(db.Model):
    """Question bank item with rubric, expected concepts, and difficulty."""
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_roles.id', ondelete='CASCADE'), index=True, nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), index=True, nullable=False)
    question_type = db.Column(db.String(30), nullable=False)  # 'technical', 'hr', 'code-written'
    difficulty = db.Column(db.String(20), nullable=False)  # 'easy', 'medium', 'hard'
    question_text = db.Column(db.Text, nullable=False)
    expected_concepts = db.Column(db.JSON, nullable=False)  # List of expected concepts / synonyms
    reference_answer = db.Column(db.Text, nullable=False)
    rubric = db.Column(db.JSON, nullable=False)  # Criterion rubrics
    max_score = db.Column(db.Float, default=10.0, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    origin = db.Column(db.String(30), default='seed', nullable=False)  # 'seed', 'admin', 'ai_generated'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    job_role = db.relationship('JobRole', back_populates='questions')
    skill = db.relationship('Skill', back_populates='questions')
    session_questions = db.relationship('SessionQuestion', back_populates='question')

    def __repr__(self):
        return f'<Question {self.id}: [{self.difficulty}][{self.question_type}] role={self.job_role_id} skill={self.skill_id}>'
