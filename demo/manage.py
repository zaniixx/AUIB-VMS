"""Simple dev CLI for VMS
Usage:
  python manage.py init-db     # Initialize database schema
  python manage.py seed        # Seed database with sample data
  python manage.py setup       # Initialize database AND seed with sample data
  python manage.py runserver   # Start development server
"""
import sys

def init_db():
    from Backend import create_app
    app = create_app()
    with app.app_context():
        from Backend.db import init_db, get_db
        # init_db already called by create_app; ensure tables exist
        print('Database initialized (create_all performed at app startup).')
        print("\n📝 Demo Credentials (run 'python manage.py seed' to populate):")
        print("   Admin:        admin@auib.edu / admin123")
        print("   Officer:      officer@auib.edu / officer123")
        print("   Club Leader:  leader.tech@auib.edu / leader123")
        print("   Student:      student@auib.edu / student123")


def seed():
    from Backend import create_app
    app = create_app()
    with app.app_context():
        # Use the comprehensive seeding from seed_data.py instead of the basic one
        from demo.seed_data import main as seed_main
        seed_main()


def setup():
    """Initialize database and seed with sample data"""
    from Backend import create_app
    app = create_app()
    with app.app_context():
        from Backend.db import init_db, get_db
        # init_db already called by create_app; ensure tables exist
        print('Database initialized (create_all performed at app startup).')
        
        # Use the comprehensive seeding from seed_data.py
        from demo.seed_data import main as seed_main
        seed_main()


def runserver():
    from Backend import create_app
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
        elif cmd == 'setup':
            setup()
        elif cmd == 'runserver':
            runserver()
        else:
            help_text()
