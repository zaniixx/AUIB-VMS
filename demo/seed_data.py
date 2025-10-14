"""
Seed script to populate database with dummy data for testing.
Run with: python seed_data.py
"""

import sys
import os
from datetime import datetime, timedelta
import time
import subprocess
from sqlalchemy import delete, text
from random import choice, randint, sample
from werkzeug.security import generate_password_hash

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vms import create_app
from vms.db import get_db
from vms.models import User, Event, TimeLog, EmailLog, Setting, gen_id


def clear_database():
    """Clear all existing data"""
    print("🗑️  Clearing existing data...")
    db = get_db()
    
    # Delete in order to respect foreign key constraints (SQLAlchemy 2.0 style)
    db.execute(delete(EmailLog))
    db.execute(delete(TimeLog))
    db.execute(delete(Event))
    db.execute(delete(User))
    db.execute(delete(Setting))

    db.commit()
    print("✅ Database cleared")


def seed_users():
    """Create sample users with different roles"""
    print("\n👥 Creating users...")
    db = get_db()
    
    users = [
        # Admin
        User(
            id=gen_id('u_'),
            email='admin@auib.edu',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            name='Admin User',
            club_id=None
        ),
        
        # Officers
        User(
            id=gen_id('u_'),
            email='officer@auib.edu',
            password_hash=generate_password_hash('officer123'),
            role='officer',
            name='Sarah Johnson',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='officer2@auib.edu',
            password_hash=generate_password_hash('officer123'),
            role='officer',
            name='Michael Chen',
            club_id=None
        ),
        
        # Club Leaders
        User(
            id=gen_id('u_'),
            email='leader.tech@auib.edu',
            password_hash=generate_password_hash('leader123'),
            role='club_leader',
            name='Emily Davis',
            club_id='club_tech'
        ),
        User(
            id=gen_id('u_'),
            email='leader.arts@auib.edu',
            password_hash=generate_password_hash('leader123'),
            role='club_leader',
            name='James Wilson',
            club_id='club_arts'
        ),
        User(
            id=gen_id('u_'),
            email='leader.sports@auib.edu',
            password_hash=generate_password_hash('leader123'),
            role='club_leader',
            name='Maria Garcia',
            club_id='club_sports'
        ),
        
        # Students/Volunteers
        User(
            id=gen_id('u_'),
            email='student@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='Alex Thompson',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='john.doe@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='John Doe',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='jane.smith@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='Jane Smith',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='bob.brown@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='Bob Brown',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='alice.jones@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='Alice Jones',
            club_id=None
        ),
        User(
            id=gen_id('u_'),
            email='charlie.miller@auib.edu',
            password_hash=generate_password_hash('student123'),
            role='student',
            name='Charlie Miller',
            club_id=None
        ),
    ]
    
    db.add_all(users)
    db.commit()
    
    print(f"✅ Created {len(users)} users:")
    print("   - Admin: admin@auib.edu (password: admin123)")
    print("   - Officers: officer@auib.edu, officer2@auib.edu (password: officer123)")
    print("   - Club Leaders: leader.tech@auib.edu, leader.arts@auib.edu, leader.sports@auib.edu (password: leader123)")
    print("   - Students: student@auib.edu, john.doe@auib.edu, jane.smith@auib.edu, etc. (password: student123)")
    
    return users


def seed_events(users):
    """Create sample events"""
    print("\n📅 Creating events...")
    db = get_db()
    
    # Get officers
    officers = [u for u in users if u.role == 'officer']
    if not officers:
        print("❌ No officers found, skipping events")
        return []
    
    officer = officers[0]
    now = datetime.now()
    
    events = [
        # Past Events
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Campus Cleanup Drive',
            start_ts=now - timedelta(days=30),
            end_ts=now - timedelta(days=30) + timedelta(hours=3),
            location='Main Campus',
            description='Community service event to clean up the campus grounds and plant new trees.',
            created_at=now - timedelta(days=35)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Food Bank Volunteer Day',
            start_ts=now - timedelta(days=20),
            end_ts=now - timedelta(days=20) + timedelta(hours=4),
            location='Community Food Bank',
            description='Help sort and distribute food to families in need.',
            created_at=now - timedelta(days=25)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Tutoring Session - Math',
            start_ts=now - timedelta(days=10),
            end_ts=now - timedelta(days=10) + timedelta(hours=2),
            location='Library Room 201',
            description='Volunteer tutoring for high school students in mathematics.',
            created_at=now - timedelta(days=15)
        ),
        
        # Active/Current Events
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Beach Cleanup Initiative',
            start_ts=now - timedelta(days=1),
            end_ts=now + timedelta(days=2),
            location='City Beach',
            description='Join us for a weekend beach cleanup to protect marine life and beautify our coastline.',
            created_at=now - timedelta(days=10)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Senior Center Visit',
            start_ts=now,
            end_ts=now + timedelta(days=1),
            location='Sunshine Senior Center',
            description='Spend time with elderly residents, play games, and share stories.',
            created_at=now - timedelta(days=7)
        ),
        
        # Upcoming Events
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Animal Shelter Volunteer Day',
            start_ts=now + timedelta(days=5),
            end_ts=now + timedelta(days=5) + timedelta(hours=4),
            location='Happy Paws Animal Shelter',
            description='Help care for animals, clean kennels, and walk dogs at the local shelter.',
            created_at=now - timedelta(days=3)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Charity 5K Run/Walk',
            start_ts=now + timedelta(days=10),
            end_ts=now + timedelta(days=10) + timedelta(hours=3),
            location='City Park',
            description='Participate in or volunteer at our annual charity run to raise funds for education.',
            created_at=now - timedelta(days=5)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Community Garden Project',
            start_ts=now + timedelta(days=15),
            end_ts=now + timedelta(days=15) + timedelta(hours=5),
            location='Community Garden Site',
            description='Help build and plant a new community garden for local residents.',
            created_at=now - timedelta(days=2)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Literacy Program - Reading Buddies',
            start_ts=now + timedelta(days=20),
            end_ts=now + timedelta(days=20) + timedelta(hours=2),
            location='Elementary School',
            description='Read with elementary school children and help improve their literacy skills.',
            created_at=now - timedelta(days=1)
        ),
        Event(
            id=gen_id('e_'),
            officer_id=officer.id,
            name='Hospital Gift Shop Volunteer',
            start_ts=now + timedelta(days=25),
            end_ts=now + timedelta(days=25) + timedelta(hours=4),
            location='City General Hospital',
            description='Assist in the hospital gift shop and provide support to patients and families.',
            created_at=now
        ),
    ]
    
    db.add_all(events)
    db.commit()
    
    print(f"✅ Created {len(events)} events:")
    print(f"   - {sum(1 for e in events if e.start_ts < now - timedelta(days=3))} past events")
    print(f"   - {sum(1 for e in events if now - timedelta(days=3) <= e.start_ts <= now + timedelta(days=3))} active events")
    print(f"   - {sum(1 for e in events if e.start_ts > now + timedelta(days=3))} upcoming events")
    
    return events


def seed_timelogs(users, events):
    """Create sample timelogs (volunteer hours)"""
    print("\n⏱️  Creating timelogs...")
    db = get_db()
    
    # Get students
    students = [u for u in users if u.role == 'student']
    if not students or not events:
        print("❌ No students or events found, skipping timelogs")
        return []
    
    now = datetime.now()
    timelogs = []
    
    # For past events, create completed timelogs with various statuses
    past_events = [e for e in events if e.end_ts and e.end_ts < now - timedelta(days=3)]
    for event in past_events:
        # Random 3-6 students volunteered for each past event
        event_volunteers = sample(students, min(randint(3, 6), len(students)))
        
        for student in event_volunteers:
            status = choice(['APPROVED', 'APPROVED', 'APPROVED', 'PENDING', 'REJECTED'])  # Bias toward approved
            hours = round(randint(2, 5) + (randint(0, 9) / 10), 1)  # 2.0 - 5.9 hours
            
            # Use real datetimes for start/stop (Postgres TIMESTAMP compatible)
            timelog = TimeLog(
                id=gen_id('t_'),
                student_email=student.email,
                event_id=event.id,
                start_ts=event.start_ts if event.start_ts else None,
                stop_ts=event.end_ts if event.end_ts else None,
                calculated_hours=hours if status == 'APPROVED' else None,
                status=status,
                marker=None
            )
            timelogs.append(timelog)
    
    # For active events, create some signed-up students (pending timelogs)
    active_events = [e for e in events if e.start_ts and now - timedelta(days=3) <= e.start_ts <= now + timedelta(days=3)]
    for event in active_events:
        event_volunteers = sample(students, min(randint(2, 5), len(students)))
        
        for student in event_volunteers:
            timelog = TimeLog(
                id=gen_id('t_'),
                student_email=student.email,
                event_id=event.id,
                start_ts=event.start_ts if event.start_ts else None,
                stop_ts=None,  # Not completed yet
                calculated_hours=None,
                status='PENDING',
                marker='signup'
            )
            timelogs.append(timelog)
    
    # For upcoming events, create signups
    upcoming_events = [e for e in events if e.start_ts and e.start_ts > now + timedelta(days=3)]
    for event in upcoming_events[:5]:  # Just first 5 upcoming events
        event_volunteers = sample(students, min(randint(1, 4), len(students)))
        
        for student in event_volunteers:
            timelog = TimeLog(
                id=gen_id('t_'),
                student_email=student.email,
                event_id=event.id,
                start_ts=None,
                stop_ts=None,
                calculated_hours=None,
                status='PENDING',
                marker='signup'
            )
            timelogs.append(timelog)
    
    db.add_all(timelogs)
    db.commit()
    
    print(f"✅ Created {len(timelogs)} timelogs:")
    completed = sum(1 for t in timelogs if t.status == 'APPROVED')
    pending = sum(1 for t in timelogs if t.status == 'PENDING')
    rejected = sum(1 for t in timelogs if t.status == 'REJECTED')
    print(f"   - {completed} approved")
    print(f"   - {pending} pending")
    print(f"   - {rejected} rejected")
    
    return timelogs


def seed_email_logs(users, events):
    """Create sample email logs"""
    print("\n📧 Creating email logs...")
    db = get_db()
    
    students = [u for u in users if u.role == 'student']
    if not students or not events:
        print("❌ No students or events found, skipping email logs")
        return []
    
    now = datetime.now()
    email_logs = []
    
    # Create email logs for past events
    for event in events[:6]:  # First 6 events
        # Send invitation emails to some students
        recipients = sample(students, min(randint(2, 4), len(students)))
        
        for student in recipients:
            status = choice(['SENT', 'SENT', 'SENT', 'FAILED'])  # Bias toward sent
            
            email_log = EmailLog(
                id=gen_id('em_'),
                recipient=student.email,
                subject=f'Volunteer Invitation: {event.name}',
                body_preview=f'You are invited to volunteer for {event.name} at {event.location}. Click the link to log hours...',
                status=status,
                error='SMTP connection timeout' if status == 'FAILED' else None,
                event_id=event.id,
                created_at=event.created_at
            )
            email_logs.append(email_log)
    
    # Add some general notification emails
    general_emails = [
        EmailLog(
            id=gen_id('em_'),
            recipient='student@auib.edu',
            subject='Welcome to AUIB VMS',
            body_preview='Welcome to the AUIB Volunteer Management System. Start tracking your volunteer hours today!',
            status='SENT',
            error=None,
            event_id=None,
            created_at=now - timedelta(days=40)
        ),
        EmailLog(
            id=gen_id('em_'),
            recipient='john.doe@auib.edu',
            subject='Password Reset Request',
            body_preview='You requested a password reset. Click the link below to set a new password.',
            status='SENT',
            error=None,
            event_id=None,
            created_at=now - timedelta(days=15)
        ),
    ]
    email_logs.extend(general_emails)
    
    db.add_all(email_logs)
    db.commit()
    
    print(f"✅ Created {len(email_logs)} email logs:")
    sent = sum(1 for e in email_logs if e.status == 'SENT')
    failed = sum(1 for e in email_logs if e.status == 'FAILED')
    print(f"   - {sent} sent")
    print(f"   - {failed} failed")
    
    return email_logs


def seed_settings():
    """Create sample settings"""
    print("\n⚙️  Creating settings...")
    db = get_db()
    
    settings = [
        Setting(key='SMTP_HOST', value='smtp.gmail.com'),
        Setting(key='SMTP_PORT', value='587'),
        Setting(key='SMTP_USE_TLS', value='1'),
        Setting(key='SMTP_USERNAME', value='noreply@auib.edu'),
        Setting(key='MAIL_DEFAULT_SENDER', value='AUIB VMS <noreply@auib.edu>'),
        Setting(key='JWT_EXP_HOURS', value='24'),
        Setting(key='SYSTEM_NAME', value='AUIB Volunteer Management System'),
    ]
    
    db.add_all(settings)
    db.commit()
    
    print(f"✅ Created {len(settings)} settings")
    
    return settings


def main():
    """Main seed function"""
    print("\n" + "="*60)
    print("🌱 AUIB VMS Database Seeding Script")
    print("="*60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Wait for DB to be available (useful in containerized environments)
        max_attempts = 12
        attempt = 0
        while attempt < max_attempts:
            try:
                db = get_db()
                # lightweight check
                db.execute(text("SELECT 1"))
                break
            except Exception as e:
                attempt += 1
                wait = 2 ** min(attempt, 6)
                print(f"Waiting for DB ({attempt}/{max_attempts})... retry in {wait}s")
                time.sleep(wait)
        else:
            print("❌ Timed out waiting for the database to become available")
            return

        # Run DB migrations if alembic is present
        if os.path.exists('alembic.ini'):
            try:
                print("⚙️  Found alembic.ini — running migrations: alembic upgrade head")
                subprocess.run(['alembic', 'upgrade', 'head'], check=True)
            except Exception as e:
                print(f"⚠️  Running alembic failed: {e}")
                print("Continuing to seed (ensure schema exists)")
        # Non-interactive seeding: proceed without prompting
        print("\n⚠️  Non-interactive mode: proceeding to clear and seed the database")

        # Clear existing data
        clear_database()
        
        # Seed data
        users = seed_users()
        events = seed_events(users)
        timelogs = seed_timelogs(users, events)
        email_logs = seed_email_logs(users, events)
        settings = seed_settings()
        
        print("\n" + "="*60)
        print("✅ Database seeding completed successfully!")
        print("="*60)
        print("\n📝 Quick Login Credentials:")
        print("   Admin:        admin@auib.edu / admin123")
        print("   Officer:      officer@auib.edu / officer123")
        print("   Club Leader:  leader.tech@auib.edu / leader123")
        print("   Student:      student@auib.edu / student123")
        print("\n🚀 You can now start the application and test with this data!")
        print("="*60 + "\n")


if __name__ == '__main__':
    main()
