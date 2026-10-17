from app.models.user import User
from app.models.job import JobRole, Skill
from app.models.question import Question


def test_cli_create_admin(runner, app):
    """Test flask create-admin CLI command provisions admin."""
    with app.app_context():
        res = runner.invoke(args=[
            'create-admin',
            '--email', 'cli_admin@example.com',
            '--password', 'AdminPass123!@#',
            '--name', 'CLI SuperAdmin'
        ])
        assert res.exit_code == 0
        assert 'provisioned successfully' in res.output

        user = User.query.filter_by(email='cli_admin@example.com').first()
        assert user is not None
        assert user.is_admin
        assert user.profile.full_name == 'CLI SuperAdmin'
        assert user.check_password('AdminPass123!@#')


def test_cli_reset_password(runner, app, candidate_user):
    """Test flask reset-password CLI command updates password."""
    with app.app_context():
        res = runner.invoke(args=[
            'reset-password',
            '--email', candidate_user.email,
            '--password', 'BrandNewPassword999!'
        ])
        assert res.exit_code == 0
        assert 'Password reset for' in res.output

        user = User.query.filter_by(email=candidate_user.email).first()
        assert user.check_password('BrandNewPassword999!')


def test_cli_seed_data(runner, app):
    """Test flask seed-data CLI command runs and creates default roles and questions."""
    with app.app_context():
        res = runner.invoke(args=['seed-data'])
        assert res.exit_code == 0
        assert 'Seed data populated successfully' in res.output

        # Verify job roles exist
        assert JobRole.query.filter_by(slug='python-developer').first() is not None
        assert JobRole.query.filter_by(slug='java-developer').first() is not None
        assert JobRole.query.filter_by(slug='data-analyst').first() is not None

        # Verify skills exist
        assert Skill.query.count() >= 8
        # Verify question bank seeded with approved questions
        assert Question.query.count() >= 60
