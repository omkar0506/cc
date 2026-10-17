from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Decorator to require that current_user is authenticated and has admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied: Administrator privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def candidate_required(f):
    """Decorator to require that current_user is authenticated and has candidate role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_candidate:
            flash('Access denied: Candidate account required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
