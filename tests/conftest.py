import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User, CandidateProfile


@pytest.fixture(scope='session')
def app():
    """Create application configured for testing."""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def db(app):
    """Provide a pristine isolated database for every test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Test client bound to isolated DB."""
    return app.test_client()


@pytest.fixture
def runner(app, db):
    """CLI test runner bound to isolated DB."""
    return app.test_cli_runner()


@pytest.fixture
def candidate_user(db):
    """Create a sample candidate user with profile."""
    user = User(email='candidate_test@example.com', role='candidate', is_active=True)
    user.set_password('CandidateSecret123!')
    db.session.add(user)
    db.session.flush()

    profile = CandidateProfile(
        user_id=user.id,
        full_name='Test Candidate',
        headline='Aspiring Engineer'
    )
    db.session.add(profile)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    """Create a sample admin user."""
    admin = User(email='admin_test@example.com', role='admin', is_active=True)
    admin.set_password('AdminSecret123!')
    db.session.add(admin)
    db.session.flush()

    profile = CandidateProfile(user_id=admin.id, full_name='System Admin')
    db.session.add(profile)
    db.session.commit()
    return admin
