from app.extensions import db
from app.models.base import utc_now


class LearningItem(db.Model):
    """Personalized learning checklist item derived from skill gaps with priority ranking."""
    __tablename__ = 'learning_items'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    suggested_resource_type = db.Column(db.String(100), nullable=True)  # e.g., 'Documentation & Practice', 'Code Exercise'
    priority_score = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'completed'
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    candidate = db.relationship('User', back_populates='learning_items')
    session = db.relationship('InterviewSession', back_populates='learning_items')
    skill = db.relationship('Skill')

    def __repr__(self):
        return f'<LearningItem {self.id}: topic={self.topic} status={self.status} priority={self.priority_score}>'
