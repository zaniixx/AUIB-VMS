from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

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
    # replace legacy `date` string with explicit start/end timestamps
    start_ts = Column(DateTime, nullable=True)
    end_ts = Column(DateTime, nullable=True)
    location = Column(String)
    description = Column(Text)
    volunteer_limit = Column(Integer, nullable=True)  # Maximum number of volunteers allowed
    # Additional event parameters
    category = Column(String, nullable=True)  # Event category (community, environmental, etc.)
    contact_name = Column(String, nullable=True)  # Event coordinator name
    contact_email = Column(String, nullable=True)  # Event coordinator email
    required_skills = Column(Text, nullable=True)  # Required skills for volunteers
    equipment_needed = Column(Text, nullable=True)  # Equipment/supplies needed
    min_age = Column(Integer, nullable=True)  # Minimum age requirement
    max_age = Column(Integer, nullable=True)  # Maximum age limit
    priority = Column(String, default='normal')  # Event priority (low, normal, high, urgent)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def display_date(self):
        # return a friendly single-line representation of start/end
        try:
            if self.start_ts and self.end_ts:
                if self.start_ts.date() == self.end_ts.date():
                    return f"{self.start_ts.strftime('%Y-%m-%d %H:%M')} - {self.end_ts.strftime('%H:%M')}"
                return f"{self.start_ts.strftime('%Y-%m-%d %H:%M')} - {self.end_ts.strftime('%Y-%m-%d %H:%M')}"
            if self.start_ts:
                return self.start_ts.strftime('%Y-%m-%d %H:%M')
            return ''
        except Exception:
            return str(self.start_ts or '')


# Utility helpers (compat shim for previous in-memory helpers)
import re
import uuid
from werkzeug.security import generate_password_hash
from .db import get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
AUIB_EMAIL_RE = re.compile(r"^[^@\s]+@auib\.edu\.iq$", re.IGNORECASE)


def is_valid_email(e):
    """Validate email format and ensure it's an AUIB email address."""
    email = (e or '').strip().lower()
    return bool(EMAIL_RE.match(email) and AUIB_EMAIL_RE.match(email))


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
    status = Column(String, default='PENDING')  # PENDING, APPROVED, REJECTED, PARTIALLY_APPROVED
    hours_data = Column(Text)  # store JSON serialized with individual approval status
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BulkSubmissionEntry(Base):
    __tablename__ = 'bulk_submission_entries'
    id = Column(String, primary_key=True)
    bulk_submission_id = Column(String, ForeignKey('bulk_submissions.id'))
    name = Column(String)
    email = Column(String)
    hours = Column(Float)
    role = Column(String)  # What the member did
    status = Column(String, default='PENDING')  # PENDING, APPROVED, REJECTED
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


class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(String, primary_key=True)
    submitter_id = Column(String, ForeignKey('users.id'), nullable=False)
    assigned_officer_id = Column(String, ForeignKey('users.id'), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # suggestion, problem, bug, feature_request, general
    priority = Column(String, default='normal')  # low, normal, high, urgent
    status = Column(String, default='open')  # open, in_progress, resolved, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status_display(self):
        return {
            'open': 'Open',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed'
        }.get(self.status, self.status)

    @property
    def priority_display(self):
        return {
            'low': 'Low',
            'normal': 'Normal',
            'high': 'High',
            'urgent': 'Urgent'
        }.get(self.priority, self.priority)

    @property
    def category_display(self):
        return {
            'suggestion': 'Suggestion',
            'problem': 'Problem',
            'bug': 'Bug Report',
            'feature_request': 'Feature Request',
            'general': 'General Inquiry'
        }.get(self.category, self.category)


class TicketResponse(Base):
    __tablename__ = 'ticket_responses'
    id = Column(String, primary_key=True)
    ticket_id = Column(String, ForeignKey('tickets.id'), nullable=False)
    responder_id = Column(String, ForeignKey('users.id'), nullable=False)
    response_text = Column(Text, nullable=False)
    is_internal = Column(Integer, default=0)  # 0=public, 1=internal note
    created_at = Column(DateTime, default=datetime.utcnow)


class TicketAttachment(Base):
    __tablename__ = 'ticket_attachments'
    id = Column(String, primary_key=True)
    ticket_id = Column(String, ForeignKey('tickets.id'), nullable=False)
    response_id = Column(String, ForeignKey('ticket_responses.id'), nullable=True)  # NULL for ticket attachments
    uploader_id = Column(String, ForeignKey('users.id'), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Relative path from upload directory
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship('Ticket', backref='attachments')
    response = relationship('TicketResponse', backref='attachments')
    uploader = relationship('User')


# Utility functions for ID generation
def gen_id(prefix=''):
    """Generate a unique ID with optional prefix"""
    return prefix + str(uuid.uuid4())


def next_timelog_id():
    """Generate a unique timelog ID"""
    return gen_id('tl_')


def next_bulk_id():
    """Generate a unique bulk submission ID"""
    return gen_id('b_')


def next_ticket_id():
    """Generate a unique ticket ID"""
    return gen_id('tk_')

