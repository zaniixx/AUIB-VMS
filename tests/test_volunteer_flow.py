import os
import pytest
from Backend import create_app
from Backend.db import init_db, get_db
from Backend.models import gen_id
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """
    Test fixture using PostgreSQL database.
    Requires DATABASE_URL environment variable to be set to a PostgreSQL test database.
    Example: postgresql://user:password@localhost:5432/vms_test
    """
    # Ensure DATABASE_URL is set for PostgreSQL
    if 'DATABASE_URL' not in os.environ or not os.environ['DATABASE_URL'].startswith('postgresql'):
        pytest.skip("PostgreSQL DATABASE_URL required for tests")
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
    })

    # Clean up test data after test
    yield app

    # Optional: Clean up test database tables
    try:
        db = get_db()
        # Add cleanup logic here if needed
    except Exception:
        pass

@pytest.fixture
def client(app):
    return app.test_client()


def test_register_login_dashboard_signup(app, client):
    # Register a new volunteer
    resp = client.post('/register', data={'email': 'volunteer@example.com', 'password': 'password123', 'name': 'Test Vol'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Registration successful' in resp.data

    # Login
    resp = client.post('/login', data={'email': 'volunteer@example.com', 'password': 'password123'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Logged in' in resp.data

    # Create an event directly in DB
    db = get_db()
    eid = gen_id('e_')
    from Backend.models import Event
    ev = Event(id=eid, name='Test Event', start_ts=None, end_ts=None, location='Room 1')
    db.add(ev)
    db.commit()

    # Access dashboard
    resp = client.get('/volunteer/dashboard')
    assert resp.status_code == 200
    assert b'Volunteer Dashboard' in resp.data

    # Sign up for event
    resp = client.post('/volunteer/signup', data={'event_id': eid}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Signed up for event' in resp.data

    # Check TimeLog was created
    from Backend.models import TimeLog
    tl = db.query(TimeLog).filter_by(event_id=eid, student_email='volunteer@example.com').first()
    assert tl is not None
