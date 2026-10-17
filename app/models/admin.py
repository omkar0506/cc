from app.extensions import db
from app.models.base import utc_now


class HumanScore(db.Model):
    """Admin manual evaluation scoring for human-versus-AI agreement benchmarking and corrections."""
    __tablename__ = 'human_scores'

    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    human_score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=10.0)
    notes = db.Column(db.Text, nullable=True)
    is_correction = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    answer = db.relationship('Answer', back_populates='human_scores')
    admin = db.relationship('User')

    def __repr__(self):
        return f'<HumanScore id={self.id} answer={self.answer_id} score={self.human_score}/{self.max_score}>'


class AuditLog(db.Model):
    """Immutable audit trail for all security, admin corrections, and privileged actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'EVALUATION_CORRECTION', 'SETTINGS_UPDATE', 'ADMIN_CREATE'
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship('User', back_populates='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} by user={self.user_id}>'


class AppSetting(db.Model):
    """Dynamic application settings: rubric weights, adaptive thresholds, caps, and feature flags."""
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, index=True, nullable=False)
    setting_value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    @classmethod
    def get_setting(cls, key: str, default=None):
        """Helper to get a setting value with fallback."""
        record = cls.query.filter_by(setting_key=key).first()
        return record.setting_value if record else default

    @classmethod
    def set_setting(cls, key: str, value, description: str = None):
        """Helper to set or update a setting value."""
        record = cls.query.filter_by(setting_key=key).first()
        if not record:
            record = cls(setting_key=key, setting_value=value, description=description)
            db.session.add(record)
        else:
            record.setting_value = value
            if description:
                record.description = description
        db.session.commit()
        return record

    def __repr__(self):
        return f'<AppSetting {self.setting_key}>'
