import os
import pytest
from Backend import create_app
from Backend.db import get_db
from Backend.models import gen_id
from werkzeug.security import generate_password_hash


def make_user(db, email, role):
    uid = gen_id('u_')
    User = __import__('vms.models', fromlist=['User']).User
    u = User(id=uid, email=email, password_hash=generate_password_hash('pass123'), role=role, name='Test')
    db.add(u)
    db.commit()
    return u


def test_home_pages_for_roles():
    """
    Test home pages for different roles using PostgreSQL.
    Requires DATABASE_URL environment variable to be set to a PostgreSQL test database.
    Example: postgresql://user:password@localhost:5432/vms_test
    """
    if 'DATABASE_URL' not in os.environ or not os.environ['DATABASE_URL'].startswith('postgresql'):
        pytest.skip("PostgreSQL DATABASE_URL required for tests")
    
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # guest view
    resp = client.get('/')
    assert b'Welcome to AUIB VMS' in resp.data

    # create and login as volunteer
    db = get_db()
    make_user(db, 'vol@example.com', 'student')
    client.post('/login', data={'email': 'vol@example.com', 'password': 'pass123'}, follow_redirects=True)
    resp = client.get('/')
    assert b'Your Volunteer Home' in resp.data
    client.get('/logout')

    # officer
    db = get_db()
    make_user(db, 'off@example.com', 'officer')
    client.post('/login', data={'email': 'off@example.com', 'password': 'pass123'}, follow_redirects=True)
    resp = client.get('/')
    assert b'Officer Home' in resp.data
    client.get('/logout')

    # admin
    db = get_db()
    make_user(db, 'admin@example.com', 'admin')
    client.post('/login', data={'email': 'admin@example.com', 'password': 'pass123'}, follow_redirects=True)
    resp = client.get('/')
    assert b'Admin Home' in resp.data
    client.get('/logout')

    # club leader
    db = get_db()
    make_user(db, 'club@example.com', 'club_leader')
    client.post('/login', data={'email': 'club@example.com', 'password': 'pass123'}, follow_redirects=True)
    resp = client.get('/')
    assert b'Club Leader Home' in resp.data
    client.get('/logout')
