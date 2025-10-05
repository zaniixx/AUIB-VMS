from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .db import get_db
from . import models
from .email import send_email
from werkzeug.security import generate_password_hash

bp = Blueprint('admin', __name__)


def admin_required():
    if not current_user or not getattr(current_user, 'role', None) in ('officer', 'admin'):
        return False
    return True


def admin_only():
    """Return True if current_user is an admin (strict)."""
    return current_user and getattr(current_user, 'role', None) == 'admin'


@bp.route('/')
@login_required
def index():
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    total_users = db.query(models.User).count()
    total_events = db.query(models.Event).count()
    total_emails = db.query(models.EmailLog).count()
    return render_template('admin/index.html', users=total_users, events=total_events, emails=total_emails)


@bp.route('/settings', methods=('GET','POST'))
@login_required
def settings():
    # allow officers to view settings, but only admins can POST changes
    if not admin_required():
        return render_template('403.html'), 403
    if request.method == 'POST':
        if not admin_only():
            return render_template('403.html'), 403
        # save settings to DB
        keys = ['SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS','SMTP_USE_TLS','SMTP_USE_SSL','MAIL_DEFAULT_SENDER']
        for k in keys:
            v = request.form.get(k.lower())
            models.set_setting(k, v)
        flash('Settings saved')
        return redirect(url_for('admin.settings'))
    # read current settings
    cfg = {}
    for k in ['SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASS','SMTP_USE_TLS','SMTP_USE_SSL','MAIL_DEFAULT_SENDER']:
        cfg[k] = models.get_setting(k) or ''
    return render_template('admin/settings.html', cfg=cfg)


@bp.route('/settings/history')
@login_required
def settings_history():
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    audits = db.query(models.SettingAudit).order_by(models.SettingAudit.changed_at.desc()).limit(200).all()
    return render_template('admin/settings_history.html', audits=audits)


@bp.route('/test-mail', methods=('POST',))
@login_required
def test_mail():
    if not admin_only():
        return render_template('403.html'), 403
    to = request.form.get('to') or current_user.email
    subj = request.form.get('subject') or 'VMS test'
    body = request.form.get('body') or 'This is a test message from VMS admin.'
    try:
        # use send_email (which reads config from app env)
        send_email(subj, body, to, async_send=False, event_id=None)
        flash(f'Test email sent to {to} (check MailHog or SMTP).')
    except Exception as e:
        current_app.logger.exception('Test mail failed')
        flash(f'Failed to send test email: {e}')
    return redirect(url_for('admin.settings'))


@bp.route('/email-logs')
@login_required
def email_logs():
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    # filters
    page = int(request.args.get('page') or 1)
    per_page = int(request.args.get('per_page') or 25)
    status = request.args.get('status')
    q = (request.args.get('q') or '').strip()
    start = request.args.get('start')
    end = request.args.get('end')

    query = db.query(models.EmailLog)
    if status:
        query = query.filter(models.EmailLog.status == status)
    if q:
        query = query.filter(models.EmailLog.recipient.ilike(f"%{q}%"))
    if start:
        try:
            from datetime import datetime
            sdt = datetime.fromisoformat(start)
            query = query.filter(models.EmailLog.created_at >= sdt)
        except Exception:
            pass
    if end:
        try:
            from datetime import datetime
            edt = datetime.fromisoformat(end)
            query = query.filter(models.EmailLog.created_at <= edt)
        except Exception:
            pass

    total = query.count()
    logs = query.order_by(models.EmailLog.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    # simple pagination helpers
    def url_for_page(p):
        args = request.args.to_dict()
        args['page'] = p
        return url_for('admin.email_logs', **args)

    return render_template('admin/email_logs.html', logs=logs, page=page, per_page=per_page, total=total, url_for_page=url_for_page, status=status, q=q, start=start, end=end)


@bp.route('/users')
@login_required
def users():
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    page = int(request.args.get('page') or 1)
    per_page = int(request.args.get('per_page') or 25)
    q = (request.args.get('q') or '').strip()
    query = db.query(models.User)
    if q:
        query = query.filter(models.User.email.ilike(f"%{q}%"))
    total = query.count()
    users = query.order_by(models.User.email).offset((page-1)*per_page).limit(per_page).all()

    def url_for_page(p):
        args = request.args.to_dict()
        args['page'] = p
        return url_for('admin.users', **args)

    return render_template('admin/users.html', users=users, page=page, per_page=per_page, total=total, url_for_page=url_for_page, q=q)


@bp.route('/users/add', methods=('GET','POST'))
@login_required
def add_user():
    if not admin_required():
        return render_template('403.html'), 403
    pre_role = request.args.get('role')
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        name = request.form.get('name')
        role = request.form.get('role') or 'student'
        club_id = request.form.get('club_id') or None
        password = request.form.get('password') or 'changeme'
        db = get_db()
        if db.query(models.User).filter_by(email=email).first():
            flash('User with that email already exists')
            return redirect(url_for('admin.add_user'))
        uid = models.gen_id('u_')
        user = models.User(id=uid, email=email, name=name, role=role, club_id=club_id, password_hash=generate_password_hash(password))
        db.add(user)
        db.commit()
        flash('User created')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', action='Add', user=None, prefill_role=pre_role)


@bp.route('/users/<user_id>/edit', methods=('GET','POST'))
@login_required
def edit_user(user_id):
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        flash('User not found')
        return redirect(url_for('admin.users'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        name = request.form.get('name')
        role = request.form.get('role')
        club_id = request.form.get('club_id') or None
        password = request.form.get('password')
        user.email = email
        user.name = name
        user.role = role
        user.club_id = club_id
        if password:
            user.password_hash = generate_password_hash(password)
        db.commit()
        flash('User updated')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', action='Edit', user=user)


@bp.route('/users/<user_id>/delete', methods=('POST',))
@login_required
def delete_user(user_id):
    if not admin_required():
        return render_template('403.html'), 403
    db = get_db()
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        flash('User not found')
        return redirect(url_for('admin.users'))
    db.delete(user)
    db.commit()
    flash('User deleted')
    return redirect(url_for('admin.users'))


@bp.route('/users/<user_id>/promote', methods=('POST',))
@login_required
def promote_user(user_id):
    if not admin_only():
        return render_template('403.html'), 403
    db = get_db()
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        flash('User not found')
        return redirect(url_for('admin.users'))
    user.role = 'admin'
    db.commit()
    flash(f'User {user.email} promoted to admin')
    return redirect(url_for('admin.users'))


@bp.route('/users/<user_id>/demote', methods=('POST',))
@login_required
def demote_user(user_id):
    if not admin_only():
        return render_template('403.html'), 403
    db = get_db()
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        flash('User not found')
        return redirect(url_for('admin.users'))
    # demote to officer by default
    user.role = 'officer'
    db.commit()
    flash(f'User {user.email} demoted to officer')
    return redirect(url_for('admin.users'))
