from flask import Blueprint, render_template, request, flash, current_app, abort, redirect, url_for
from flask_login import login_required, current_user
import json
import pandas as pd
import os
from werkzeug.utils import secure_filename

from . import models
from .db import get_db

bp = Blueprint('club', __name__)


@bp.route('/submit_hours', methods=['GET','POST'])
@login_required
def submit_hours():
    if current_user.role != 'club_leader':
        abort(403)
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        date_range = request.form.get('date_range')
        description = request.form.get('description')

        # Check if file was uploaded
        if 'hours_file' not in request.files:
            flash('No file uploaded')
            return render_template('submit_hours.html')

        file = request.files['hours_file']
        if file.filename == '':
            flash('No file selected')
            return render_template('submit_hours.html')

        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            flash('Invalid file type. Please upload .xlsx, .xls, or .csv file')
            return render_template('submit_hours.html')

        try:
            # Read the file
            if file.filename.lower().endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Validate required columns
            required_columns = ['name', 'email', 'hours', 'role']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}')
                return render_template('submit_hours.html')

            # Process and validate data
            entries = []
            errors = []

            for idx, row in df.iterrows():
                try:
                    name = str(row['name']).strip()
                    email = str(row['email']).strip().lower()
                    hours = float(row['hours'])
                    role = str(row['role']).strip()

                    # Validate email format and domain
                    if not email.endswith('@auib.edu.iq'):
                        errors.append(f'Row {idx+2}: Email must end with @auib.edu.iq: {email}')
                        continue

                    if not models.is_valid_email(email):
                        errors.append(f'Row {idx+2}: Invalid email format: {email}')
                        continue

                    if hours <= 0:
                        errors.append(f'Row {idx+2}: Hours must be positive: {hours}')
                        continue

                    if not name or not role:
                        errors.append(f'Row {idx+2}: Name and role are required')
                        continue

                    entries.append({
                        'name': name,
                        'email': email,
                        'hours': hours,
                        'role': role
                    })

                except Exception as e:
                    errors.append(f'Row {idx+2}: Error processing data - {str(e)}')

            if errors:
                flash('Validation errors found:<br>' + '<br>'.join(errors))
                return render_template('submit_hours.html')

            if not entries:
                flash('No valid entries found in the file')
                return render_template('submit_hours.html')

            # Create bulk submission
            b_id = models.next_bulk_id()
            db = get_db()

            # Create bulk submission
            sub = models.BulkSubmission(
                id=b_id,
                club_leader_id=current_user.id,
                project_name=project_name,
                date_range=date_range,
                description=description,
                status='PENDING'
            )
            db.add(sub)

            # Create individual entries
            for entry in entries:
                entry_id = models.gen_id('be_')
                bulk_entry = models.BulkSubmissionEntry(
                    id=entry_id,
                    bulk_submission_id=b_id,
                    name=entry['name'],
                    email=entry['email'],
                    hours=entry['hours'],
                    role=entry['role'],
                    status='PENDING'
                )
                db.add(bulk_entry)

            db.commit()
            flash(f'Bulk submission created with {len(entries)} entries pending officer approval')
            return redirect(url_for('club.my_submissions'))

        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return render_template('submit_hours.html')

    return render_template('submit_hours.html')


@bp.route('/my_submissions')
@login_required
def my_submissions():
    if current_user.role != 'club_leader':
        abort(403)
    db = get_db()
    submissions = db.query(models.BulkSubmission).filter_by(club_leader_id=current_user.id).order_by(models.BulkSubmission.created_at.desc()).all()

    # Add computed fields for template
    for s in submissions:
        # Get entries for this submission
        entries = db.query(models.BulkSubmissionEntry).filter_by(bulk_submission_id=s.id).all()
        s.total_volunteers = len(entries)
        s.total_hours = sum(entry.hours for entry in entries)
        s.entries = entries  # Add entries to submission object

        # Count approved/rejected entries
        s.approved_count = sum(1 for entry in entries if entry.status == 'APPROVED')
        s.rejected_count = sum(1 for entry in entries if entry.status == 'REJECTED')
        s.pending_count = sum(1 for entry in entries if entry.status == 'PENDING')

    return render_template('my_submissions.html', submissions=submissions)
