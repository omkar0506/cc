import os
import click
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, limiter


def create_app(config_name=None):
    """Application factory for AI-Powered Adaptive Interviewer."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Ensure private storage directory exists
    storage_dir = app.config.get('STORAGE_DIR')
    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)

    # Register blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.candidate import candidate_bp
    from app.admin import admin_bp
    from app.jobs import jobs_bp
    from app.interviews import interviews_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(interviews_bp)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_cli_commands(app)

    return app


def register_error_handlers(app):
    """Register HTTP error pages."""
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html', error=error), 500


def register_cli_commands(app):
    """Register custom Flask CLI management commands."""
    from app.models.user import User, CandidateProfile
    from app.models.admin import AuditLog

    @app.cli.command('create-admin')
    @click.option('--email', prompt='Admin email', help='Admin email address')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
    @click.option('--name', prompt='Admin full name', default='Administrator', help='Admin full name')
    def create_admin(email, password, name):
        """CLI command to safely provision an administrator."""
        email = email.lower().strip()
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Error: User with email {email} already exists.")
            return

        admin_user = User(email=email, role='admin', is_active=True)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.flush()

        profile = CandidateProfile(user_id=admin_user.id, full_name=name)
        db.session.add(profile)

        audit = AuditLog(
            user_id=admin_user.id,
            action='ADMIN_PROVISIONED_VIA_CLI',
            target_type='users',
            target_id=str(admin_user.id),
            details={'email': email}
        )
        db.session.add(audit)
        db.session.commit()

        click.echo(f"Success: Administrator {email} provisioned successfully.")

    @app.cli.command('reset-password')
    @click.option('--email', prompt='User email', help='Email of account to reset')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
    def reset_password(email, password):
        """CLI command to securely reset an account password."""
        email = email.lower().strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            click.echo(f"Error: User with email {email} not found.")
            return

        user.set_password(password)
        audit = AuditLog(
            user_id=user.id,
            action='PASSWORD_RESET_VIA_CLI',
            target_type='users',
            target_id=str(user.id),
            details={'email': email}
        )
        db.session.add(audit)
        db.session.commit()

        click.echo(f"Success: Password reset for {email}.")

    @app.cli.command('seed-data')
    def seed_data_command():
        """CLI command to populate seed data into the database."""
        from scripts.seed_data import seed_all
        seed_all()
        click.echo("Seed data populated successfully.")
