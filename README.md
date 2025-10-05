AUIB Volunteers Management System (VMS) - README
===============================================

Overview
--------
This repository contains a prototype AUIB Volunteers Management System (VMS) built in Python/Flask.
The project was delivered first as a single-file `app.py`, then refactored into a modular package `ves/`.

This README explains how to run the app on Windows (PowerShell), including a robust fallback to handle venv/ensurepip issues.

Prerequisites
-------------
- Python 3.10+ (tested with Python 3.13.7)
- Windows PowerShell (examples below assume PowerShell)
- Internet access to download packages (for pip installs)

Files of interest
-----------------
 - `app.py` - application entrypoint (calls `vms.create_app()`)
 - `vms/` - package containing the application modules (renamed from `ves`)
  - `vms/models.py` - SQLAlchemy ORM models and helper utilities
  - `vms/auth.py` - authentication/login and home route
  - `vms/officer.py` - officer actions (event creation, approvals, reports)
  - `vms/club.py` - club leader flows (bulk submissions)
  - `vms/log.py` - JWT link handling and volunteer clocking
- `templates/` - Jinja2 templates used by the app
- `requirements.txt` - pip dependencies

Quick start (recommended)
-------------------------
Open PowerShell in repository root (where this README is located).

1) Create and activate a venv (preferred, try the normal method first):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) If the `venv` command hangs at ensurepip or fails, use the fallback below (safe):

Fallback (works around ensurepip hang):

```powershell
# Create venv without pip (avoids ensurepip)
python -m venv .venv --without-pip

# Download get-pip.py
Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py

# Install pip into the new venv
.\.venv\Scripts\python.exe get-pip.py

# Activate the venv
.\.venv\Scripts\Activate.ps1
```

3) Install dependencies

```powershell
pip install -r requirements.txt
```

4) Run the app

```powershell
python app.py
```

5) Open in your browser

- Open http://127.0.0.1:5000
- Login page: http://127.0.0.1:5000/login

Seeded users (for demo):
- Officer: officer@auib.edu / officerpass
- Club leader: leader@club.auib / leaderpass
- Student: student@auib.edu / studentpass

Developer shortcuts
-------------------
You can use the provided `manage.py` script for common tasks in development.

Create DB (create_all) and initialize app:

```powershell
$env:PYTHONPATH = (Get-Location).Path; python manage.py init-db
```

Seed demo users:

```powershell
$env:PYTHONPATH = (Get-Location).Path; python manage.py seed
```

Run dev server using the CLI:

```powershell
$env:PYTHONPATH = (Get-Location).Path; python manage.py runserver
```

To bootstrap a developer environment (create venv, install, and seed) use the `setup.ps1` script:

```powershell
# create venv only (dry-run installs skipped)
powershell -ExecutionPolicy Bypass -File .\setup.ps1

# create venv and install packages
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Install

# create venv, install packages and seed demo users
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Install -Seed
```

Email configuration
-------------------
The app supports sending emails using Flask-Mailman (recommended). To enable automatic sending of JWT links, set these environment variables before starting the app:

- `SMTP_HOST` — SMTP server host (e.g. smtp.sendgrid.net)
- `SMTP_PORT` — SMTP server port (e.g. 587)
- `SMTP_USER` — SMTP username (if required)
- `SMTP_PASS` — SMTP password (if required)
- `SMTP_USE_TLS` — set to `1` to enable STARTTLS
- `SMTP_USE_SSL` — set to `1` to enable SSL socket
- `MAIL_DEFAULT_SENDER` — optional default From address

If `flask-mailman` is not installed, the app will fall back to displaying generated links and will log that email features are disabled. For production, use a transactional email provider and a secrets manager for credentials.


Demo flows
----------
1) Officer: Create Event & Generate Links
- Login as officer
- Go to "Create Event & Generate Links"
- Upload a CSV or Excel file that contains a column named `Email` or `email`.
  - Example CSV:
    email,Name
    student@auib.edu,Student One
    volunteer2@example.com,Volunteer Two
- The page will display generated time-bound URLs (simulate sending via email).

2) Volunteer: Use the link
- Open one of the generated links
- If no open session: click "Start" to clock-in (records start timestamp)
- If open session exists: click "Stop" to clock-out; hours are calculated and stored

3) Club Leader: Bulk Submission
- Login as club leader
- Go to "Submit Bulk Hours"
- Provide JSON hours list in the textarea, e.g.:
  [
    {"email": "student@auib.edu", "hours": 3.5},
    {"email": "another@auib.edu", "hours": 2}
  ]
- Submission will be saved with status `PENDING`

4) Officer: Approve Bulk Submission
- Login as officer
- Go to "Approve Bulk Submissions"
- Approve a submission: approved hours become APPROVED timelogs with event_id like `BULK_<id>`
- Reject: requires a reason and sets status to `REJECTED`

Reports
-------
Officers can generate CSV reports at `/officer/reports`.
Supported report types:
- `general` - all approved timelogs merged with event/project names
- `person_summary` - single-row summary of total lifetime approved hours for a student (requires `student_email` filter)
- `person_detailed` - every approved timelog for a student (requires `student_email` filter)

Troubleshooting
---------------
- If `python -m venv` hangs at ensurepip:
  - Use the `--without-pip` fallback and install pip manually with get-pip.py (see Fallback section).
  - Check your antivirus or endpoint protection: temporarily disable it and retry venv creation if permitted.
  - Ensure you have network access to pypi and bootstrap URLs; if your network blocks downloads, install packages offline or via a mirror.

- If templates fail to render or you see import errors:
  - Ensure you're running the app from the repository root (so Flask can find `templates/` and `ves/`).
  - Activate the venv so the installed packages are used.

Security notes
--------------
 - The JWT secret and Flask secret are hardcoded for development. For production, set `VMS_SECRET_KEY` and `VMS_JWT_SECRET` environment variables to strong secrets.
- This prototype uses in-memory data structures (dictionaries). For production, switch to a real database (SQLAlchemy + PostgreSQL/SQLite) and follow standard migration and backup practices.

Development notes
-----------------
- To run tests or add persistence, I can add simple pytest tests and a JSON-based persistence layer.
- A `setup.ps1` script can be added to automate the fallback venv creation and pip install steps; tell me if you want that.

Contact
-------
If you want me to add a `setup.ps1` script, persist data to disk, or add tests/integration examples, say which you'd prefer and I'll implement it.
