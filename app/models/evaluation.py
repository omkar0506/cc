from app.extensions import db
from app.models.base import utc_now


class Evaluation(db.Model):
    """Answer-level evaluation with explicit rubrics, criterion breakdown, and evidence quotes."""
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'), unique=True, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    score_ratio = db.Column(db.Float, nullable=False)  # total_score / max_score
    criterion_scores = db.Column(db.JSON, nullable=False)  # Schema-validated dict of scores per criterion
    supporting_quotes = db.Column(db.JSON, nullable=True)  # List of exact quotes from the candidate answer
    criterion_explanations = db.Column(db.JSON, nullable=True)  # Detailed explanation per rubric criterion
    missing_concepts = db.Column(db.JSON, nullable=True)  # Concepts expected but missing
    strengths = db.Column(db.JSON, nullable=True)  # List of specific strength bullet points
    improvement_suggestions = db.Column(db.JSON, nullable=True)  # Actionable suggestions
    suggested_followup = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(50), default='rule_based', nullable=False)  # 'rule_based', 'gemini', 'openai'
    model = db.Column(db.String(50), nullable=True)
    tokens_used = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(30), default='completed', nullable=False)  # 'completed', 'pending', 'failed', 'corrected'
    error_message = db.Column(db.Text, nullable=True)
    evaluated_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    answer = db.relationship('Answer', back_populates='evaluation')

    def __repr__(self):
        return f'<Evaluation {self.id} for answer={self.answer_id} score={self.total_score}/{self.max_score} ({self.provider})>'


class SkillEvidence(db.Model):
    """Signature feature: Resume claim vs self-rating vs demonstrated evidence analysis."""
    __tablename__ = 'skill_evidence'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'skill_id', name='uq_session_skill_evidence'),
    )

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
    resume_claim = db.Column(db.Boolean, default=False, nullable=False)
    resume_snippet = db.Column(db.Text, nullable=True)
    self_rating = db.Column(db.Integer, nullable=True)  # 1 to 5
    job_importance = db.Column(db.Float, default=1.0, nullable=False)
    questions_tested_count = db.Column(db.Integer, default=0, nullable=False)
    average_score_ratio = db.Column(db.Float, nullable=True)
    # 4 distinct evidence states:
    # 'Demonstrated', 'Partially demonstrated', 'Needs further assessment', 'Not yet assessed'
    status = db.Column(db.String(35), nullable=False, default='Not yet assessed')
    sufficiency_note = db.Column(db.Text, nullable=False)
    recommended_next_assessment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    candidate = db.relationship('User', back_populates='skill_evidence')
    session = db.relationship('InterviewSession', back_populates='skill_evidence')
    skill = db.relationship('Skill', back_populates='evidence_records')

    def __repr__(self):
        return f'<SkillEvidence session={self.session_id} skill={self.skill_id} status={self.status}>'
