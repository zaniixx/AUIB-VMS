from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    name = Column(String)
    club_id = Column(String, nullable=True)

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class Event(Base):
    __tablename__ = 'events'
    id = Column(String, primary_key=True)
    officer_id = Column(String, ForeignKey('users.id'))
    name = Column(String)
    date = Column(String)
    location = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Utility helpers (compat shim for previous in-memory helpers)
import re
import uuid
from werkzeug.security import generate_password_hash
from .db import get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(e):
    return bool(EMAIL_RE.match((e or '').strip()))


def gen_id(prefix=''):
    return prefix + str(uuid.uuid4())


def next_event_id():
    return gen_id('e_')


def next_timelog_id():
    return gen_id('t_')


def next_bulk_id():
    return gen_id('b_')


def get_user(user_id):
    db = get_db()
    return db.query(User).filter_by(id=user_id).first()


def find_user_by_email(email):
    if not email:
        return None
    db = get_db()
    return db.query(User).filter_by(email=email.lower()).first()


def seed_sample_users():
    db = get_db()
    # if any users exist, assume seeded
    if db.query(User).first():
        return
    u1 = User(id=gen_id('u_'), email='officer@auib.edu', password_hash=generate_password_hash('officerpass'), role='officer', name='Officer One')
    u2 = User(id=gen_id('u_'), email='leader@club.auib', password_hash=generate_password_hash('leaderpass'), role='club_leader', name='Leader One', club_id=gen_id('club_'))
    u3 = User(id=gen_id('u_'), email='student@auib.edu', password_hash=generate_password_hash('studentpass'), role='student', name='Student One')
    db.add_all([u1, u2, u3])
    db.commit()


def record_email_log(recipient, subject, body_preview, status='QUEUED', error=None, event_id=None):
    db = get_db()
    from datetime import datetime
    log = EmailLog(id=gen_id('em_'), recipient=recipient, subject=subject, body_preview=(body_preview or '')[:200], status=status, error=error, event_id=event_id, created_at=datetime.utcnow())
    db.add(log)
    db.commit()
    return log


def get_setting(key):
    db = get_db()
    s = db.query(Setting).filter_by(key=key).first()
    return s.value if s else None


def set_setting(key, value):
    db = get_db()
    s = db.query(Setting).filter_by(key=key).first()
    old = s.value if s else None
    if s:
        s.value = value
    else:
        s = Setting(key=key, value=value)
        db.add(s)
    db.commit()

    # record audit entry
    try:
        # avoid importing flask at module import time; get current user if available
        changed_by = None
        try:
            from flask_login import current_user
            if current_user and getattr(current_user, 'is_authenticated', False):
                changed_by = getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        except Exception:
            changed_by = None
        audit = SettingAudit(id=gen_id('sa_'), key=key, old_value=old, new_value=value, changed_by=changed_by)
        db.add(audit)
        db.commit()
    except Exception:
        try:
            # swallow errors to avoid blocking the setting change
            db.rollback()
        except Exception:
            pass

    # If SMTP-related setting changed, clear the email module's SMTP cache so
    # new settings are used immediately without restarting the app.
    try:
        from .email import clear_smtp_cache
        if key.startswith('SMTP_') or key == 'MAIL_DEFAULT_SENDER':
            clear_smtp_cache()
    except Exception:
        # don't let settings update fail because email module isn't available
        pass

    return s


class TimeLog(Base):
    __tablename__ = 'timelogs'
    id = Column(String, primary_key=True)
    student_email = Column(String, index=True)
    event_id = Column(String, ForeignKey('events.id'))
    start_ts = Column(String)
    stop_ts = Column(String)
    calculated_hours = Column(Float)
    status = Column(String, default='PENDING')
    marker = Column(String, nullable=True)


class BulkSubmission(Base):
    __tablename__ = 'bulk_submissions'
    id = Column(String, primary_key=True)
    club_leader_id = Column(String, ForeignKey('users.id'))
    project_name = Column(String)
    date_range = Column(String)
    description = Column(Text)
    status = Column(String, default='PENDING')
    hours_data = Column(Text)  # store JSON serialized
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = 'email_logs'
    id = Column(String, primary_key=True)
    recipient = Column(String, index=True)
    subject = Column(String)
    body_preview = Column(Text)
    status = Column(String)  # SENT, FAILED, QUEUED
    error = Column(Text, nullable=True)
    event_id = Column(String, ForeignKey('events.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(Text)


class SettingAudit(Base):
    __tablename__ = 'setting_audits'
    id = Column(String, primary_key=True)
    key = Column(String, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

 