from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models.user import User, CandidateProfile
from app.models.admin import AuditLog
from app.auth.forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_safe_url(target):
    """Prevent open redirect vulnerabilities."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Authenticate candidates and administrators."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('candidate.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)

            # Record login in audit log
            audit = AuditLog(
                user_id=user.id,
                action='USER_LOGIN',
                target_type='users',
                target_id=str(user.id),
                details={'role': user.role},
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            db.session.commit()

            flash(f'Welcome back, {user.profile.full_name if user.profile else user.email}!', 'success')

            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('candidate.dashboard'))
        else:
            flash('Invalid email address or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new candidate account."""
    if current_user.is_authenticated:
        return redirect(url_for('candidate.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User(email=email, role='candidate', is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # obtain user.id

        # Create candidate profile
        profile = CandidateProfile(
            user_id=user.id,
            full_name=form.full_name.data.strip()
        )
        db.session.add(profile)

        # Audit registration
        audit = AuditLog(
            user_id=user.id,
            action='USER_REGISTERED',
            target_type='users',
            target_id=str(user.id),
            details={'email': email, 'role': 'candidate'},
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        flash('Your account has been successfully created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """End the user session."""
    user_id = current_user.id
    audit = AuditLog(
        user_id=user_id,
        action='USER_LOGOUT',
        target_type='users',
        target_id=str(user_id),
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))
