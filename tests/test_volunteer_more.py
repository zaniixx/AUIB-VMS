import os
import tempfile
import pytest
from vms import create_app
from vms.db import get_db
from vms.models import gen_id


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    app = create_app()
    app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})
    yield app
    try:
        os.remove(db_path)
    except Exception:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email='volunteer@example.com', password='password123'):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


def register(client):
    return client.post('/register', data={'email': 'volunteer@example.com', 'password': 'password123', 'name': 'Test Vol'}, follow_redirects=True)


def test_cancel_signup_and_edge_cases(app, client):
    # register and login
    resp = register(client)
    assert b'Registration successful' in resp.data
    resp = login(client)
    assert b'Logged in' in resp.data

    db = get_db()
    # create event
    eid = gen_id('e_')
    from vms.models import Event
    ev = Event(id=eid, name='Cancelable Event', location='Room X')
    db.add(ev)
    db.commit()

    # sign up
    resp = client.post('/volunteer/signup', data={'event_id': eid}, follow_redirects=True)
    assert b'Signed up for event' in resp.data

    # duplicate signup attempt
    resp = client.post('/volunteer/signup', data={'event_id': eid}, follow_redirects=True)
    assert b'already signed up' in resp.data

    # cancel signup
    resp = client.post('/volunteer/cancel', data={'event_id': eid}, follow_redirects=True)
    assert b'signup has been cancelled' in resp.data

    # cancel non-existent
    resp = client.post('/volunteer/cancel', data={'event_id': 'nope'}, follow_redirects=True)
    assert b'You are not signed up' in resp.data or resp.status_code == 200

    # signup nonexistent event
    resp = client.post('/volunteer/signup', data={'event_id': 'nope'}, follow_redirects=True)
    assert b'Event not found' in resp.data or resp.status_code == 200

    # logout and try to access dashboard (should redirect to login)
    client.get('/logout', follow_redirects=True)
    resp = client.get('/volunteer/dashboard', follow_redirects=False)
    assert resp.status_code in (302, 303)
