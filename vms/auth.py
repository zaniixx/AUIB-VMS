from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, current_user, login_required

from .models import seed_sample_users
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


@bp.app_context_processor
def inject_current_user():
    return dict(current_user=current_user)
 