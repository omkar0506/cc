from app.extensions import db
from app.models.base import utc_now


class Resume(db.Model):
    """Candidate uploaded resume record with extraction metadata and file tracking."""
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), default='application/pdf', nullable=False)
    parsed_text = db.Column(db.Text, nullable=True)
    extracted_data = db.Column(db.JSON, nullable=True)  # Structured suggestion dict
    status = db.Column(db.String(30), default='uploaded', nullable=False)  # uploaded, parsed, confirmed, failed
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='resumes')
    extracted_skills = db.relationship(
        'ResumeSkill',
        back_populates='resume',
        cascade='all, delete-orphan'
    )
    interview_sessions = db.relationship('InterviewSession', back_populates='resume')

    def __repr__(self):
        return f'<Resume {self.id}: {self.original_filename} ({self.status})>'


class ResumeSkill(db.Model):
    """Candidate-confirmable skill claims extracted from a resume with verbatim text snippets."""
    __tablename__ = 'resume_skills'
    __table_args__ = (
        db.UniqueConstraint('resume_id', 'skill_id', name='uq_resume_skill'),
    )

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='RESTRICT'), nullable=False)
    claimed_name = db.Column(db.String(100), nullable=False)
    evidence_snippet = db.Column(db.Text, nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    candidate_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    resume = db.relationship('Resume', back_populates='extracted_skills')
    skill = db.relationship('Skill', back_populates='resume_skills')

    def __repr__(self):
        return f'<ResumeSkill resume={self.resume_id} skill={self.skill_id} confirmed={self.is_confirmed}>'
