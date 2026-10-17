from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.models.base import utc_now


class User(UserMixin, db.Model):
    """User account model supporting candidate and admin roles."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), default='candidate', nullable=False)  # 'candidate', 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    profile = db.relationship(
        'CandidateProfile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan'
    )
    resumes = db.relationship(
        'Resume',
        back_populates='user',
        cascade='all, delete-orphan',
        order_by='Resume.created_at.desc()'
    )
    interview_sessions = db.relationship(
        'InterviewSession',
        back_populates='candidate',
        cascade='all, delete-orphan',
        order_by='InterviewSession.created_at.desc()'
    )
    skill_evidence = db.relationship(
        'SkillEvidence',
        back_populates='candidate',
        cascade='all, delete-orphan'
    )
    learning_items = db.relationship(
        'LearningItem',
        back_populates='candidate',
        cascade='all, delete-orphan'
    )
    audit_logs = db.relationship(
        'AuditLog',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def set_password(self, password: str):
        """Hashes the password securely with scrypt/pbkdf2."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies candidate or admin password against the hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def is_candidate(self) -> bool:
        return self.role == 'candidate'

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    if not user_id:
        return None
    return db.session.get(User, int(user_id))


class CandidateProfile(db.Model):
    """Detailed profile for candidate users."""
    __tablename__ = 'candidate_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    headline = db.Column(db.String(255), nullable=True)
    education_level = db.Column(db.String(100), nullable=True)  # e.g., B.Tech / B.E., M.Tech, B.S.
    institution = db.Column(db.String(200), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = db.relationship('User', back_populates='profile')

    def __repr__(self):
        return f'<CandidateProfile {self.full_name}>'
