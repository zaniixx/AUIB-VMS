"""Simple dev CLI for VMS
Usage:
  python manage.py init-db
  python manage.py seed
  python manage.py runserver
"""
import sys

def init_db():
    from vms import create_app
    app = create_app()
    with app.app_context():
        from vms.db import init_db, get_db
        # init_db already called by create_app; ensure tables exist
        print('Database initialized (create_all performed at app startup).')


def seed():
    from vms import create_app
    app = create_app()
    with app.app_context():
        from vms.models import seed_sample_users
        seed_sample_users()
        print('Seeded sample users')


def runserver():
    from vms import create_app
    app = create_app()
    app.run(debug=True, port=5000)


def help_text():
    print(__doc__)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        help_text()
    else:
        cmd = sys.argv[1]
        if cmd == 'init-db':
            init_db()
        elif cmd == 'seed':
            seed()
        elif cmd == 'runserver':
            runserver()
        else:
            help_text()
