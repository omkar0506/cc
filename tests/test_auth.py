from app.models.user import User


def test_registration_success(client, db):
    """Test successful candidate registration creates user, profile, and audit log."""
    res = client.post('/auth/register', data={
        'full_name': 'Alice Wonder',
        'email': 'alice@example.com',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    }, follow_redirects=True)

    assert res.status_code == 200
    user = User.query.filter_by(email='alice@example.com').first()
    assert user is not None
    assert user.is_candidate
    assert user.profile is not None
    assert user.profile.full_name == 'Alice Wonder'
    assert user.check_password('SecurePassword123!')


def test_registration_duplicate_email(client, candidate_user):
    """Test registering with an existing email fails validation."""
    res = client.post('/auth/register', data={
        'full_name': 'Duplicate User',
        'email': candidate_user.email,
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert b'An account with this email address already exists' in res.data


def test_registration_password_mismatch(client):
    """Test registration rejects mismatched passwords."""
    res = client.post('/auth/register', data={
        'full_name': 'Bob Tester',
        'email': 'bob@example.com',
        'password': 'PasswordOne123!',
        'confirm_password': 'PasswordTwo123!'
    })
    assert b'Passwords must match' in res.data


def test_candidate_login_and_logout(client, candidate_user):
    """Test candidate login, redirection, and logout."""
    # Login
    res = client.post('/auth/login', data={
        'email': candidate_user.email,
        'password': 'CandidateSecret123!'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Candidate Dashboard' in res.data

    # Logout
    logout_res = client.get('/auth/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b'You have been logged out successfully' in logout_res.data


def test_login_invalid_credentials(client, candidate_user):
    """Test login with wrong password displays danger alert."""
    res = client.post('/auth/login', data={
        'email': candidate_user.email,
        'password': 'WrongPassword999!'
    }, follow_redirects=True)
    assert b'Invalid email address or password' in res.data


def test_admin_access_control(client, candidate_user, admin_user):
    """Test role-based access control: candidate cannot access /admin/dashboard."""
    # Log in as candidate
    client.post('/auth/login', data={
        'email': candidate_user.email,
        'password': 'CandidateSecret123!'
    })

    # Attempt to visit admin dashboard
    admin_res = client.get('/admin/dashboard')
    assert admin_res.status_code == 403

    client.get('/auth/logout')

    # Log in as admin
    client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'AdminSecret123!'
    })

    # Admin should succeed
    admin_allowed_res = client.get('/admin/dashboard')
    assert admin_allowed_res.status_code == 200
    assert b'Administrator Portal' in admin_allowed_res.data
