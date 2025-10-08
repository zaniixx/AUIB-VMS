from flask import Flask, redirect, url_for, render_template
import os
from flask_login import LoginManager

from .models import get_user, seed_sample_users
from .db import init_db

login_manager = LoginManager()


def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = os.environ.get('VMS_SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET'] = os.environ.get('VMS_JWT_SECRET', 'jwt-secret')
    app.config['JWT_ALGORITHM'] = os.environ.get('VMS_JWT_ALGORITHM', 'HS256')
    app.config['JWT_EXP_HOURS'] = int(os.environ.get('VMS_JWT_EXP_HOURS', '24'))
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vms.db'))}")

    # Mail configuration (optional)
    app.config['MAIL_SERVER'] = os.environ.get('SMTP_HOST')
    if os.environ.get('SMTP_PORT'):
        app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT'))
    if os.environ.get('SMTP_USER'):
        app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USER')
    if os.environ.get('SMTP_PASS'):
        app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASS')
    # MAIL_USE_TLS / MAIL_USE_SSL keys
    if os.environ.get('SMTP_USE_TLS'):
        app.config['MAIL_USE_TLS'] = bool(int(os.environ.get('SMTP_USE_TLS')))
    if os.environ.get('SMTP_USE_SSL'):
        app.config['MAIL_USE_SSL'] = bool(int(os.environ.get('SMTP_USE_SSL')))


    # init db
    init_db(app)

    # ensure DB sessions are removed at the end of each request/appcontext
    from .db import close_db
    @app.teardown_appcontext
    def _close_db(exception=None):
        try:
            close_db()
        except Exception:
            app.logger.exception('Error closing DB session')

    # initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return get_user(user_id)

    # register blueprints
    from .auth import bp as auth_bp
    from .officer import bp as officer_bp
    from .club import bp as club_bp
    from .log import bp as log_bp
    from .admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(officer_bp, url_prefix='/officer')
    app.register_blueprint(club_bp, url_prefix='/club')
    app.register_blueprint(log_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Add custom Jinja2 filters
    @app.template_filter('format_datetime')
    def format_datetime_filter(value):
        """Format datetime objects or ISO strings into readable format"""
        if not value:
            return '—'
        
        try:
            from datetime import datetime
            # If it's already a datetime object
            if isinstance(value, datetime):
                return value.strftime('%b %d, %Y %H:%M')
            
            # If it's a string, try to parse it
            if isinstance(value, str):
                # Handle ISO format with T separator
                if 'T' in value:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    # Try different common formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        return value  # Return as-is if can't parse
                
                return dt.strftime('%b %d, %Y %H:%M')
            
            return str(value)
        except Exception:
            return str(value) if value else '—'

    # seed users (idempotent)
    seed_sample_users()

    # initialize email subsystem if available
    try:
        from .email import init_mail
        init_mail(app)
    except Exception:
        app.logger.info('Flask-Mailman not available; email features disabled')

    @app.route('/')
    def home():
        return redirect(url_for('auth.home_page'))

    @app.errorhandler(403)
    def forbidden(error):
        # friendly forbidden page with guidance
        return render_template('403.html', error=error), 403

    @app.errorhandler(404)
    def page_not_found(error):
        # friendly 404 page with navigation options
        return render_template('404.html', error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        # friendly 500 page with support contact
        return render_template('500.html', error=error), 500

    # expose "view-as" effective role for admin previewing the frontend
    @app.context_processor
    def inject_view_as():
        try:
            from flask import session
            from flask_login import current_user
            from .db import get_db
            from . import models
        except Exception:
            return {}
        view_as_role = session.get('view_as_role')
        # allow "view-as" for admins (any role) and club leaders (student/club_leader only)
        user_role = getattr(current_user, 'role', None) if getattr(current_user, 'is_authenticated', False) else None
        is_viewing_as = False
        
        if view_as_role:
            if user_role == 'admin':
                # admins can view as any role
                is_viewing_as = True
            elif user_role in ('club_leader', 'clubleader') and view_as_role in ('student', 'club_leader', 'clubleader'):
                # club leaders can toggle between student and club_leader views
                is_viewing_as = True
        
        if is_viewing_as:
            effective_role = view_as_role
        else:
            effective_role = user_role or 'guest'
        
        # Add pending counts for officers
        pending_timelogs_count = 0
        pending_event_requests_count = 0
        pending_bulk_submissions_count = 0
        if effective_role == 'officer' and getattr(current_user, 'is_authenticated', False):
            try:
                db = get_db()
                pending_timelogs_count = db.query(models.TimeLog).filter(models.TimeLog.status == 'PENDING').count()
                pending_event_requests_count = db.query(models.TimeLog).filter(models.TimeLog.status == 'PENDING_APPROVAL').count()
                pending_bulk_submissions_count = db.query(models.BulkSubmission).filter(models.BulkSubmission.status == 'PENDING').count()
            except Exception:
                pending_timelogs_count = 0
                pending_event_requests_count = 0
                pending_bulk_submissions_count = 0
        
        return dict(view_as_role=view_as_role, is_viewing_as=is_viewing_as, effective_role=effective_role, pending_count=pending_timelogs_count + pending_event_requests_count + pending_bulk_submissions_count, pending_timelogs_count=pending_timelogs_count, pending_event_requests_count=pending_event_requests_count, pending_bulk_submissions_count=pending_bulk_submissions_count)

    return app
