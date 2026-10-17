from flask import Blueprint, render_template
from app.models.job import JobRole

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page featuring application capabilities and available job roles."""
    roles = JobRole.query.filter_by(is_active=True).all()
    return render_template('index.html', roles=roles)
