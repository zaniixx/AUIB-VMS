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

    return app
