from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, current_user, login_required

from .models import seed_sample_users, gen_id, next_timelog_id
from .db import get_db
from . import log as log_mod
from . import models
from .email import send_email
import jwt
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')
        db = get_db()
        user = db.query(getattr(__import__('vms.models', fromlist=['User']), 'User')).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, pw):
            login_user(user)
            flash('Logged in')
            return redirect(url_for('auth.home_page'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('auth.home_page'))


@bp.route('/')
def home_page():
    return render_template('home.html')


@bp.route('/forgot', methods=('GET','POST'))
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        db = get_db()
        user = db.query(models.User).filter_by(email=email).first()
        if user:
            # build a short-lived JWT reset token
            secret = current_app.config.get('JWT_SECRET') or current_app.config.get('SECRET_KEY')
            hours = int(current_app.config.get('JWT_EXP_HOURS', 2))
            payload = {'sub': user.id, 'email': user.email, 'exp': datetime.utcnow() + timedelta(hours=hours), 'type': 'pwreset'}
            token = jwt.encode(payload, secret, algorithm=current_app.config.get('JWT_ALGORITHM','HS256'))
            link = url_for('auth.reset_password', token=token, _external=True)
            # send email
            body = f"Follow this link to reset your password: {link}\nIf you didn't ask for this, ignore."
            html = current_app.jinja_env.get_template('email_reset.html').render(link=link, user=user)
            send_email('Password reset for VMS', body, user.email, html=html, async_send=True)
            flash('If that email exists we sent a reset link. Check your mail (MailHog for local dev).')
        else:
            flash('If that email exists we sent a reset link. Check your mail (MailHog for local dev).')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot.html')


@bp.route('/reset/<token>', methods=('GET','POST'))
def reset_password(token):
    secret = current_app.config.get('JWT_SECRET') or current_app.config.get('SECRET_KEY')
    try:
        data = jwt.decode(token, secret, algorithms=[current_app.config.get('JWT_ALGORITHM','HS256')])
    except Exception:
        flash('Invalid or expired reset token')
        return redirect(url_for('auth.login'))
    if data.get('type') != 'pwreset':
        flash('Invalid reset token')
        return redirect(url_for('auth.login'))
    db = get_db()
    user = db.query(models.User).filter_by(id=data.get('sub')).first()
    if not user:
        flash('User not found')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        pw = request.form.get('password')
        if not pw or len(pw) < 6:
            flash('Password must be 6+ characters')
            return redirect(request.url)
        user.password_hash = __import__('werkzeug.security', fromlist=['generate_password_hash']).generate_password_hash(pw)
        db.commit()
        flash('Password updated; please login')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset.html', token=token)


@bp.route('/register', methods=('GET','POST'))
def register():
    """Volunteer self-registration. Creates a user with role 'student'."""
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        name = (request.form.get('name') or '').strip()
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required')
            return redirect(request.url)
        if not models.is_valid_email(email):
            flash('Invalid email address')
            return redirect(request.url)
        db = get_db()
        existing = db.query(models.User).filter_by(email=email).first()
        if existing:
            flash('An account with that email already exists; try logging in')
            return redirect(url_for('auth.login'))
        uid = gen_id('u_')
        user = models.User(id=uid, email=email, password_hash=generate_password_hash(password), role='student', name=name)
        db.add(user)
        db.commit()
        login_user(user)
        flash('Registration successful — welcome!')
        return redirect(url_for('auth.volunteer_dashboard'))
    return render_template('register.html')


@bp.route('/volunteer/dashboard')
@login_required
def volunteer_dashboard():
    """Dashboard for volunteers to view past, active, and upcoming events and sign up."""
    db = get_db()
    now = datetime.utcnow()

    # Upcoming and active events
    events = db.query(models.Event).order_by(models.Event.start_ts).all()
    upcoming = [e for e in events if e.start_ts and e.start_ts > now]
    active = [e for e in events if e.start_ts and e.end_ts and e.start_ts <= now <= e.end_ts]

    # Timelogs for the current user (matched by email)
    user_email = getattr(current_user, 'email', None)
    timelogs = []
    if user_email:
        rows = db.query(models.TimeLog, models.Event).join(models.Event, models.Event.id == models.TimeLog.event_id).filter(models.TimeLog.student_email == user_email).order_by(models.Event.start_ts.desc()).all()
        for tl, ev in rows:
            timelogs.append({'timelog': tl, 'event': ev})

    # For each upcoming/active event determine if user already signed up
    def user_signed(event):
        return db.query(models.TimeLog).filter_by(student_email=user_email, event_id=event.id).first() is not None

    upcoming_info = [{'event': e, 'signed': user_signed(e)} for e in upcoming]
    active_info = [{'event': e, 'signed': user_signed(e)} for e in active]

    return render_template('volunteer/dashboard.html', upcoming=upcoming_info, active=active_info, past=timelogs)


@bp.route('/volunteer/signup', methods=('POST',))
@login_required
def signup_event():
    event_id = request.form.get('event_id')
    if not event_id:
        flash('No event specified')
        return redirect(url_for('auth.volunteer_dashboard'))
    db = get_db()
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        flash('Event not found')
        return redirect(url_for('auth.volunteer_dashboard'))
    user_email = getattr(current_user, 'email', None)
    if not user_email:
        flash('Your account has no email associated; cannot sign up')
        return redirect(url_for('auth.volunteer_dashboard'))
    # prevent duplicate signups
    existing = db.query(models.TimeLog).filter_by(student_email=user_email, event_id=event_id).first()
    if existing:
        flash('You are already signed up for that event')
        return redirect(url_for('auth.volunteer_dashboard'))
    tid = next_timelog_id()
    tl = models.TimeLog(id=tid, student_email=user_email, event_id=event_id, start_ts=None, stop_ts=None, status='SIGNED_UP')
    db.add(tl)
    db.commit()
    flash('Signed up for event — good luck!')
    return redirect(url_for('auth.volunteer_dashboard'))


@bp.app_context_processor
def inject_current_user():
    return dict(current_user=current_user)
