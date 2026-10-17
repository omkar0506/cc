from app.extensions import db
from app.models.base import utc_now


class JobRole(db.Model):
    """Job role definition with target skills, topics, and difficulty distribution."""
    __tablename__ = 'job_roles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(150), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    experience_level = db.Column(db.String(50), nullable=False, default='Entry-Level')
    interview_topics = db.Column(db.JSON, nullable=True, default=list)  # List of string topics
    difficulty_distribution = db.Column(db.JSON, nullable=True, default=lambda: {'easy': 30, 'medium': 50, 'hard': 20})
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    role_skills = db.relationship(
        'JobRoleSkill',
        back_populates='job_role',
        cascade='all, delete-orphan',
        order_by='JobRoleSkill.importance_weight.desc()'
    )
    questions = db.relationship(
        'Question',
        back_populates='job_role',
        cascade='all, delete-orphan'
    )
    interview_sessions = db.relationship(
        'InterviewSession',
        back_populates='job_role'
    )

    def __repr__(self):
        return f'<JobRole {self.title}>'


class Skill(db.Model):
    """Normalized skill registry with alias support for resume matching."""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, index=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, index=True, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='technical')  # technical, hr, situational
    description = db.Column(db.Text, nullable=True)
    aliases = db.Column(db.JSON, nullable=True)  # List of synonym/variant strings
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    role_skills = db.relationship('JobRoleSkill', back_populates='skill', cascade='all, delete-orphan')
    questions = db.relationship('Question', back_populates='skill')
    resume_skills = db.relationship('ResumeSkill', back_populates='skill')
    evidence_records = db.relationship('SkillEvidence', back_populates='skill')

    def __repr__(self):
        return f'<Skill {self.name}>'


class JobRoleSkill(db.Model):
    """Association table linking job roles to target skills with weights and requirement flags."""
    __tablename__ = 'job_role_skills'
    __table_args__ = (
        db.UniqueConstraint('job_role_id', 'skill_id', name='uq_job_role_skill'),
    )

    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_roles.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    importance_weight = db.Column(db.Float, default=1.0, nullable=False)  # Scale typically 1.0 to 5.0
    is_required = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    job_role = db.relationship('JobRole', back_populates='role_skills')
    skill = db.relationship('Skill', back_populates='role_skills')

    def __repr__(self):
        return f'<JobRoleSkill role={self.job_role_id} skill={self.skill_id} w={self.importance_weight}>'
