AUIB Volunteers Management System (VMS) - README
===============================================

Overview
--------
This repository contains the AUIB Volunteers Management System (VMS) built with Python/Flask and PostgreSQL.
The system provides a comprehensive platform for managing volunteer activities, time tracking, event management,
and reporting for the American University in Bulgaria.

The application supports multiple user roles (Admin, Officers, Club Leaders, Students) with role-based access control,
JWT-based authentication for volunteer time tracking, and a complete workflow for event creation, volunteer registration,
time logging, and reporting.

Technology Stack
----------------
- **Backend**: Python 3.11+, Flask web framework
- **Database**: PostgreSQL 15
- **Authentication**: Flask-Login with JWT tokens for volunteer links
- **Email**: Flask-Mailman for SMTP integration
- **Data Processing**: Pandas for CSV/Excel file handling
- **Deployment**: Docker & Docker Compose for containerized deployment
- **Frontend**: Jinja2 templates with vanilla CSS/JavaScript

Files of interest
-----------------
 - `app.py` - application entrypoint (calls `vms.create_app()`)
 - `vms/` - package containing the application modules
  - `vms/__init__.py` - Flask app factory and configuration
  - `vms/models.py` - SQLAlchemy ORM models (User, Event, TimeLog, etc.)
  - `vms/db.py` - Database connection and initialization
  - `vms/auth.py` - authentication/login and home routes
  - `vms/admin.py` - admin panel and system settings
  - `vms/officer.py` - officer actions (event creation, approvals, reports)
  - `vms/club.py` - club leader flows (bulk submissions)
  - `vms/log.py` - JWT link handling and volunteer clocking
  - `vms/email.py` - email utilities and templates
  - `vms/static/` - CSS, JavaScript, and image assets
- `templates/` - Jinja2 HTML templates
- `seed_data.py` - database seeding script with demo data
- `requirements.txt` - Python dependencies
- `Dockerfile` & `docker-compose.yml` - containerized deployment
- `docker-compose.demo.yml` - demo environment with seeded database

Quick Start
-----------

### 🚀 Option 1: Docker Demo (Recommended)

The fastest way to see the system in action with a fully seeded database:

```bash
# Clone the repository and navigate to it
cd path/to/auib-vms

# Start the demo environment
docker-compose -f docker-compose.demo.yml up --build

# Access the application at http://localhost:8000
```

The demo includes:
- PostgreSQL database with sample data
- Pre-seeded users and events
- Fully configured environment

### 🐍 Option 2: Local Development

**Prerequisites:**
- Python 3.11 or higher
- PostgreSQL 15+ installed and running
- PostgreSQL database created (e.g., `vms`)

Open PowerShell/bash in the repository root.

1) **Set up PostgreSQL and environment variables:**

```bash
# Create PostgreSQL database
# Using psql: createdb vms

# Set DATABASE_URL environment variable (Windows PowerShell)
$env:DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/vms"

# Set DATABASE_URL environment variable (Linux/Mac)
export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/vms"
```

2) **Create and activate a virtual environment:**

```bash
# Create venv
python -m venv .venv

# Activate venv (Windows)
.venv\Scripts\Activate.ps1

# Activate venv (Linux/Mac)
source .venv/bin/activate
```

3) **Install dependencies:**

```bash
pip install -r requirements.txt
```

4) **Set up the database:**

```bash
# Initialize database (creates tables)
python manage.py init-db

# Seed with demo data
python manage.py seed
```

5) **Run the application:**

```bash
python app.py
```

5) **Open in browser:**
   - Main app: http://127.0.0.1:5000
   - Login page: http://127.0.0.1:5000/login

### 🐳 Option 3: Docker Production

For production deployment with PostgreSQL:

```bash
# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f web
```

### 🔧 Troubleshooting Virtual Environment

If `python -m venv` hangs at ensurepip:

```bash
# Create venv without pip
python -m venv .venv --without-pip

# Download get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# or on Windows PowerShell:
# Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py

# Install pip into venv
.venv\Scripts\python.exe get-pip.py

# Activate and install requirements
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Seeded Demo Users
------------------
When using the demo environment or running `python manage.py seed`, the following users are created:

### Admin
- **Email:** admin@auib.edu
- **Password:** admin123
- **Role:** System Administrator

### Officers
- **Email:** officer@auib.edu / officer2@auib.edu
- **Password:** officer123
- **Role:** University Officer (can create events, approve submissions, generate reports)

### Club Leaders
- **Email:** leader.tech@auib.edu (Technology Club)
- **Email:** leader.arts@auib.edu (Arts Club)
- **Email:** leader.sports@auib.edu (Sports Club)
- **Password:** leader123
- **Role:** Club Leader (can submit bulk volunteer hours)

### Students/Volunteers
- **Email:** student@auib.edu, john.doe@auib.edu, jane.smith@auib.edu, bob.brown@auib.edu, alice.jones@auib.edu, charlie.miller@auib.edu
- **Password:** student123
- **Role:** Student Volunteer (can log time using JWT links)

Developer Tools
---------------

### Management Commands

Use the provided `manage.py` script for common development tasks:

```bash
# Initialize database (create tables)
python manage.py init-db

# Seed database with demo data
python manage.py seed

# Run development server
python manage.py runserver

# Access Flask shell for debugging
python manage.py shell
```

### Docker Development

```bash
# Start demo environment (with seeded data)
docker-compose -f docker-compose.demo.yml up --build

# Start production environment
docker-compose up --build

# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down -v
```

### Running Tests

Tests require a PostgreSQL database connection:

```bash
# Set up test database
createdb vms_test

# Set DATABASE_URL for testing (Windows PowerShell)
$env:DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/vms_test"

# Set DATABASE_URL for testing (Linux/Mac)
export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/vms_test"

# Run tests with pytest
pytest tests/

# Run specific test file
pytest tests/test_volunteer_flow.py
```

### Automated Setup

Use the PowerShell setup script for automated environment setup:

```powershell
# Create venv only
.\setup.ps1

# Create venv and install packages
.\setup.ps1 -Install

# Create venv, install packages, and seed database
.\setup.ps1 -Install -Seed
```

Configuration
-------------

### Environment Variables

The application supports the following environment variables:

**Database:**
- `DATABASE_URL` - PostgreSQL connection string (required)
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://vms:vms_pass@localhost:5432/vms`

**Security:**
- `VMS_SECRET_KEY` - Flask secret key (required for production)
- `VMS_JWT_SECRET` - JWT signing secret (optional, defaults to Flask secret)

**Database Connection Pooling:**
- `DB_POOL_SIZE` - Connection pool size (default: 10)
- `DB_MAX_OVERFLOW` - Max overflow connections (default: 20)
- `DB_POOL_TIMEOUT` - Pool timeout in seconds (default: 60)

### Email Configuration

The app supports sending emails using Flask-Mailman. Configure SMTP settings through environment variables:

**Required:**
- `SMTP_HOST` - SMTP server host (e.g., smtp.gmail.com)
- `SMTP_PORT` - SMTP server port (e.g., 587)
- `SMTP_USER` - SMTP username/email address
- `SMTP_PASS` - SMTP password or App Password

**Optional:**
- `SMTP_USE_TLS` - Set to `1` to enable STARTTLS (recommended for port 587)
- `SMTP_USE_SSL` - Set to `1` to enable SSL socket (for port 465)
- `MAIL_DEFAULT_SENDER` - Default From address

#### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://support.google.com/accounts/answer/185833
3. Set environment variables:
   ```bash
   export SMTP_HOST=smtp.gmail.com
   export SMTP_PORT=587
   export SMTP_USER=your-gmail@gmail.com
   export SMTP_PASS=your-16-character-app-password
   export SMTP_USE_TLS=1
   ```

#### Outlook Setup
1. If you have 2FA enabled, create an App Password
2. Set environment variables:
   ```bash
   export SMTP_HOST=smtp-mail.outlook.com
   export SMTP_PORT=587
   export SMTP_USER=your-email@outlook.com
   export SMTP_PASS=your-password-or-app-password
   export SMTP_USE_TLS=1
   ```

#### Testing Email Configuration
After configuring SMTP settings, use the "Test Email Configuration" form in the admin settings page to verify your setup is working correctly.

If `flask-mailman` is not installed, the app will fall back to displaying generated links and will log that email features are disabled.


System Features
---------------

### User Roles & Permissions

- **Admin:** Full system access, user management, system settings, email configuration
- **Officer:** Event creation, volunteer link generation, bulk submission approval, reports
- **Club Leader:** Bulk volunteer hour submissions for their club members
- **Student:** Time tracking via JWT links, personal dashboard

### Demo Workflows

#### 1. Admin: System Management
- Login as admin@auib.edu / admin123
- Access admin panel at `/admin`
- Manage users, view system settings, configure email
- Monitor system activity and logs

#### 2. Officer: Event Creation & Link Generation
- Login as officer@auib.edu / officer123
- Navigate to "Create Event & Generate Links"
- Upload CSV/Excel file with volunteer emails
- System generates time-bound JWT URLs for each volunteer
- Links can be copied or emailed automatically

#### 3. Volunteer: Time Tracking
- Receive JWT link via email or direct URL
- Click "Start" to begin time tracking session
- Click "Stop" to end session and record hours
- Hours are automatically calculated and stored

#### 4. Club Leader: Bulk Hour Submission
- Login as leader.tech@auib.edu / leader123
- Navigate to "Submit Bulk Hours"
- Provide JSON array of volunteer hours:
  ```json
  [
    {"email": "student@auib.edu", "hours": 3.5},
    {"email": "john.doe@auib.edu", "hours": 2.0}
  ]
  ```
- Submissions are marked as PENDING for officer approval

#### 5. Officer: Bulk Submission Approval
- Login as officer
- Navigate to "Approve Bulk Submissions"
- Review pending submissions
- Approve or reject with optional reason
- Approved hours become permanent timelogs

Reports & Analytics
------------------
Officers can generate detailed CSV reports at `/officer/reports`:

- **General Report:** All approved timelogs with event and project details
- **Person Summary:** Lifetime approved hours summary for a specific student
- **Person Detailed:** Every approved timelog entry for a specific student

Reports support filtering by date range, event type, and volunteer email.

Database Schema
---------------
The system uses PostgreSQL with the following main tables:

- **users:** User accounts with roles and club affiliations
- **events:** Volunteer events with metadata and settings
- **timelogs:** Individual volunteer time entries
- **email_logs:** Email delivery tracking
- **settings:** System configuration values

Database migrations are handled automatically on startup using SQLAlchemy's metadata.create_all().

Deployment
----------

### Docker Production Setup

1. **Configure Environment:**
   ```bash
   # Set production secrets
   export VMS_SECRET_KEY="your-secure-flask-secret"
   export VMS_JWT_SECRET="your-secure-jwt-secret"

   # Configure email (optional)
   export SMTP_HOST="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USER="your-email@gmail.com"
   export SMTP_PASS="your-app-password"
   export SMTP_USE_TLS="1"
   ```

2. **Deploy:**
   ```bash
   docker-compose up --build -d
   ```

3. **Access:**
   - Application: http://your-server:8000
   - Database: localhost:5432 (internal only)

### Security Considerations

- Change default secrets in production
- Use strong passwords for database and admin accounts
- Configure HTTPS in production
- Regularly backup the PostgreSQL database
- Monitor logs for security events

Troubleshooting
---------------

### Virtual Environment Issues
If `python -m venv` hangs at ensurepip:
- Use the fallback method described in Quick Start
- Check antivirus/firewall blocking pip downloads
- Try using a different Python version

### Database Connection Issues
- Ensure PostgreSQL is running and accessible
- Check DATABASE_URL environment variable
- For Docker: verify container networking with `docker network ls`

### Template/Import Errors
- Ensure you're running from the repository root
- Check that all Python files are in the correct locations
- Verify virtual environment is activated

### Docker Issues
- Clear Docker cache: `docker system prune -a`
- Check container logs: `docker-compose logs`
- Ensure ports 5432 and 8000 are available

### Email Problems
- Test SMTP settings in admin panel
- Check spam folder for test emails
- Verify firewall allows SMTP port outbound

Development Notes
-----------------
- The system uses SQLAlchemy 2.0 with modern ORM patterns
- JWT tokens expire after 24 hours (configurable)
- Database schema migrations are automatic on startup
- The application requires PostgreSQL as the database backend
- Connection pooling is configured for optimal PostgreSQL performance

API Endpoints
-------------
The system provides RESTful endpoints for integration:

- `POST /api/events` - Create event and generate volunteer links
- `GET /api/reports` - Generate CSV reports
- `POST /api/bulk-submit` - Submit bulk volunteer hours
- `POST /api/approve-bulk` - Approve bulk submissions

Contributing
------------
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

License
-------
This project is developed for the American University in Iraq Baghdad

Contact
-------
For technical support or feature requests, please create an issue in the repository.
