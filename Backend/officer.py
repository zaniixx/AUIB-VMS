from flask import Blueprint, render_template, request, flash, url_for, send_file, current_app, redirect, abort, jsonify
from flask_login import login_required, current_user
import io
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
from sqlalchemy import func

from . import models
from .db import get_db

bp = Blueprint('officer', __name__)


@bp.route('/')
@login_required
def officer_index():
    return redirect(url_for('auth.home_page'))


@bp.route('/create_event', methods=['GET','POST'])
@login_required
def create_event():
    if current_user.role != 'officer':
        abort(403)
    links = None
    if request.method == 'POST':
        name = request.form.get('name')
        start_raw = request.form.get('start')
        end_raw = request.form.get('end')
        location = request.form.get('location')
        description = request.form.get('description')
        volunteer_limit = request.form.get('volunteer_limit')
        category = request.form.get('category')
        contact_name = request.form.get('contact_name')
        contact_email = request.form.get('contact_email')
        required_skills = request.form.get('required_skills')
        equipment_needed = request.form.get('equipment_needed')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        priority = request.form.get('priority', 'normal')
        entry_method = request.form.get('entry_method', 'file')
        invite_volunteers = request.form.get('invite_volunteers') == 'on'  # Checkbox to enable volunteer invitations
        
        # Convert volunteer_limit to int if provided
        volunteer_limit_int = None
        if volunteer_limit:
            try:
                volunteer_limit_int = int(volunteer_limit)
                if volunteer_limit_int <= 0:
                    volunteer_limit_int = None
            except ValueError:
                volunteer_limit_int = None
        
        # Convert age limits to int if provided
        min_age_int = None
        max_age_int = None
        if min_age:
            try:
                min_age_int = int(min_age)
            except ValueError:
                min_age_int = None
        if max_age:
            try:
                max_age_int = int(max_age)
            except ValueError:
                max_age_int = None
        
        # parse start/end timestamps from datetime-local inputs
        sd = None
        ed = None
        from datetime import datetime
        def _try_parse(s):
            if not s:
                return None
            try:
                # datetime-local typically looks like 'YYYY-MM-DDTHH:MM' or with seconds
                return datetime.fromisoformat(s)
            except Exception:
                try:
                    return datetime.fromisoformat(s.replace('T', ' '))
                except Exception:
                    return None
        sd = _try_parse(start_raw)
        ed = _try_parse(end_raw)

        # validate start exists and end is after start
        if not sd:
            flash('Start date/time is required and must be a valid datetime')
            return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
        if ed and ed < sd:
            flash('End date/time must be after start date/time')
            return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)

        # create event record with all new parameters
        import uuid
        eid = 'e_' + str(uuid.uuid4())
        db = get_db()
        ev = models.Event(
            id=eid, 
            officer_id=current_user.id, 
            name=name, 
            start_ts=sd, 
            end_ts=ed, 
            location=location, 
            description=description, 
            volunteer_limit=volunteer_limit_int,
            category=category,
            contact_name=contact_name,
            contact_email=contact_email,
            required_skills=required_skills,
            equipment_needed=equipment_needed,
            min_age=min_age_int,
            max_age=max_age_int,
            priority=priority
        )
        db.add(ev)
        db.commit()

        # Process volunteers only if invite_volunteers is checked
        volunteers_data = []
        if invite_volunteers:
            # Process volunteers based on entry method
            if entry_method == 'file':
                # File upload method
                file = request.files.get('file')
                if not file:
                    flash('File required when using file upload method')
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                
                data = file.read()
                try:
                    df = None
                    filename = file.filename.lower()
                    if filename.endswith('.csv') or file.mimetype == 'text/csv':
                        df = pd.read_csv(io.BytesIO(data))
                    else:
                        df = pd.read_excel(io.BytesIO(data))
                except Exception as e:
                    flash('Failed to read file: ' + str(e))
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                
                email_col = 'Email' if 'Email' in df.columns else ('email' if 'email' in df.columns else None)
                if not email_col:
                    flash("File must contain 'Email' column")
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                
                df['email_norm'] = df[email_col].astype(str).str.strip().str.lower()
                # try to capture a name column if present for user-friendly output
                name_col = None
                if 'Name' in df.columns:
                    name_col = 'Name'
                elif 'name' in df.columns:
                    name_col = 'name'
                df = df[df['email_norm'].apply(models.is_valid_email)]
                df = df.drop_duplicates(subset=['email_norm'])
                
                # Check volunteer limit
                if volunteer_limit_int and len(df) > volunteer_limit_int:
                    flash(f'Too many volunteers in file. Limit is {volunteer_limit_int}, file contains {len(df)}.')
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                
                for idx, row in df.iterrows():
                    e = str(row['email_norm'])
                    display_name = (str(row[name_col]).strip() if name_col and not pd.isna(row.get(name_col)) else '') if name_col else ''
                    volunteers_data.append({'email': e, 'name': display_name or e.split('@')[0]})
                    
            else:
                # Manual entry method
                volunteer_names = request.form.getlist('volunteer_names[]')
                volunteer_emails = request.form.getlist('volunteer_emails[]')
                
                if not volunteer_emails or not any(email.strip() for email in volunteer_emails):
                    flash('At least one volunteer email is required when inviting volunteers')
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                
                # Filter out empty entries
                for i, email in enumerate(volunteer_emails):
                    email = email.strip()
                    if email:
                        if not models.is_valid_email(email):
                            flash(f'Invalid email address: {email}')
                            db.delete(ev)
                            db.commit()
                            return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)
                        
                        name = volunteer_names[i].strip() if i < len(volunteer_names) else ''
                        volunteers_data.append({
                            'email': email.lower(),
                            'name': name or email.split('@')[0]
                        })
                
                # Remove duplicates
                seen_emails = set()
                unique_volunteers = []
                for v in volunteers_data:
                    if v['email'] not in seen_emails:
                        seen_emails.add(v['email'])
                        unique_volunteers.append(v)
                volunteers_data = unique_volunteers
                
                # Check volunteer limit
                if volunteer_limit_int and len(volunteers_data) > volunteer_limit_int:
                    flash(f'Too many volunteers. Limit is {volunteer_limit_int}, you entered {len(volunteers_data)}.')
                    db.delete(ev)
                    db.commit()
                    return render_template('create_event.html', links=None, name=name, start=start_raw, end=end_raw, location=location, description=description, volunteer_limit=volunteer_limit, category=category, contact_name=contact_name, contact_email=contact_email, required_skills=required_skills, equipment_needed=equipment_needed, min_age=min_age, max_age=max_age, priority=priority)

        # Generate links and send emails only if there are volunteers to invite
        links = []
        links_info = []
        sent = 0
        failed = 0
        
        if volunteers_data:
            from .log import make_logging_jwt
            email_map = {}
            
            for volunteer in volunteers_data:
                token = make_logging_jwt(eid, volunteer['email'], current_app.config.get('JWT_EXP_HOURS',24))
                link = url_for('log.log_via_jwt', jwt_token=token, _external=True)
                links.append(link)
                email_map[volunteer['email']] = link
                links_info.append({'name': volunteer['name'], 'email': volunteer['email'], 'link': link})
            
            # attempt to send emails via the configured Mail subsystem (if initialized)
            try:
                from .email import send_email
                subj = f"Logging link for event: {name}"
                default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
                # human-friendly event date for emails
                ev_display = ev.display_date if hasattr(ev, 'display_date') else (start_raw or '')
                for recipient, lnk in email_map.items():
                    body = f"Dear volunteer,\n\nYou have been invited to log volunteer hours for the event '{name}' ({ev_display}). Use the link below to start/stop your session:\n\n{lnk}\n\nThis link expires in {current_app.config.get('JWT_EXP_HOURS',24)} hours.\n\nThank you,\nAUIB VMS"
                    try:
                        send_email(subj, body, recipient, sender=default_sender, async_send=True)
                        sent += 1
                    except Exception:
                        current_app.logger.exception('Failed to queue email to %s', recipient)
                        failed += 1
            except Exception:
                current_app.logger.info('Mail subsystem not available; skipping auto-email send')

        if invite_volunteers and volunteers_data:
            flash(f'Event created with {len(links)} unique valid emails — emailed: {sent}, failed: {failed}')
        elif invite_volunteers and not volunteers_data:
            flash('Event created but no valid volunteers were found to invite')
        else:
            flash('Event created successfully! Volunteers can now sign up on their own.')

    
    # pass form defaults back to template so values persist on validation errors / after POST
    return render_template('create_event.html', 
                         links=links, 
                         links_info=(locals().get('links_info') if 'links_info' in locals() else None), 
                         name=(locals().get('name') if 'name' in locals() else None), 
                         start=(locals().get('start_raw') if 'start_raw' in locals() else None), 
                         end=(locals().get('end_raw') if 'end_raw' in locals() else None), 
                         location=(locals().get('location') if 'location' in locals() else None), 
                         description=(locals().get('description') if 'description' in locals() else None),
                         volunteer_limit=(locals().get('volunteer_limit') if 'volunteer_limit' in locals() else None),
                         category=(locals().get('category') if 'category' in locals() else None),
                         contact_name=(locals().get('contact_name') if 'contact_name' in locals() else None),
                         contact_email=(locals().get('contact_email') if 'contact_email' in locals() else None),
                         required_skills=(locals().get('required_skills') if 'required_skills' in locals() else None),
                         equipment_needed=(locals().get('equipment_needed') if 'equipment_needed' in locals() else None),
                         min_age=(locals().get('min_age') if 'min_age' in locals() else None),
                         max_age=(locals().get('max_age') if 'max_age' in locals() else None),
                         priority=(locals().get('priority') if 'priority' in locals() else 'normal'))


@bp.route('/approvals', methods=['GET','POST'])
@login_required
def approvals():
    if current_user.role != 'officer':
        abort(403)
    if request.method == 'POST':
        action = request.form.get('action')
        b_id = request.form.get('bulk_submission_id')
        entry_ids = request.form.getlist('entry_ids[]')

        db = get_db()
        sub = db.query(models.BulkSubmission).filter_by(id=b_id).first()
        if not sub:
            flash('Submission not found')
            return redirect(url_for('officer.approvals'))

        if action in ['approve_selected', 'reject_selected']:
            if not entry_ids:
                flash('No entries selected')
                return redirect(url_for('officer.approvals'))

            # Process individual entries
            approved_count = 0
            rejected_count = 0

            for entry_id in entry_ids:
                entry = db.query(models.BulkSubmissionEntry).filter_by(id=entry_id, bulk_submission_id=b_id).first()
                if entry:
                    if action == 'approve_selected':
                        # Create timelog for approved entry
                        t_id = models.next_timelog_id()
                        tl = models.TimeLog(
                            id=t_id,
                            student_email=entry.email,
                            event_id=f'BULK_{sub.id}',
                            start_ts=None,
                            stop_ts=None,
                            calculated_hours=entry.hours,
                            status='APPROVED',
                            marker='BULK'
                        )
                        db.add(tl)
                        entry.status = 'APPROVED'
                        approved_count += 1
                    elif action == 'reject_selected':
                        reason = request.form.get('rejection_reason_selected')
                        if not reason:
                            flash('Rejection reason required')
                            return redirect(url_for('officer.approvals'))
                        entry.status = 'REJECTED'
                        entry.rejection_reason = reason
                        rejected_count += 1

            # Update bulk submission status
            all_entries = db.query(models.BulkSubmissionEntry).filter_by(bulk_submission_id=b_id).all()
            approved_entries = sum(1 for e in all_entries if e.status == 'APPROVED')
            rejected_entries = sum(1 for e in all_entries if e.status == 'REJECTED')
            pending_entries = sum(1 for e in all_entries if e.status == 'PENDING')

            if pending_entries == 0:
                if approved_entries > 0 and rejected_entries == 0:
                    sub.status = 'APPROVED'
                elif approved_entries == 0 and rejected_entries > 0:
                    sub.status = 'REJECTED'
                else:
                    sub.status = 'PARTIALLY_APPROVED'
            else:
                sub.status = 'PARTIALLY_APPROVED'

            db.commit()

            if action == 'approve_selected':
                flash(f'Approved {approved_count} entries')
            else:
                flash(f'Rejected {rejected_count} entries with reason: {reason}')

        elif action == 'approve_all':
            # Approve all pending entries
            pending_entries = db.query(models.BulkSubmissionEntry).filter_by(
                bulk_submission_id=b_id, status='PENDING'
            ).all()

            for entry in pending_entries:
                t_id = models.next_timelog_id()
                tl = models.TimeLog(
                    id=t_id,
                    student_email=entry.email,
                    event_id=f'BULK_{sub.id}',
                    start_ts=None,
                    stop_ts=None,
                    calculated_hours=entry.hours,
                    status='APPROVED',
                    marker='BULK'
                )
                db.add(tl)
                entry.status = 'APPROVED'

            # Check if all entries are now approved
            all_entries = db.query(models.BulkSubmissionEntry).filter_by(bulk_submission_id=b_id).all()
            if all(e.status == 'APPROVED' for e in all_entries):
                sub.status = 'APPROVED'
            else:
                sub.status = 'PARTIALLY_APPROVED'

            db.commit()
            flash(f'Approved {len(pending_entries)} entries')

        elif action == 'reject_all':
            reason = request.form.get('rejection_reason')
            if not reason:
                flash('Rejection reason required')
                return redirect(url_for('officer.approvals'))

            # Reject all pending entries
            pending_entries = db.query(models.BulkSubmissionEntry).filter_by(
                bulk_submission_id=b_id, status='PENDING'
            ).all()

            for entry in pending_entries:
                entry.status = 'REJECTED'
                entry.rejection_reason = reason

            # Check if all entries are now rejected
            all_entries = db.query(models.BulkSubmissionEntry).filter_by(bulk_submission_id=b_id).all()
            if all(e.status == 'REJECTED' for e in all_entries):
                sub.status = 'REJECTED'
            else:
                sub.status = 'PARTIALLY_APPROVED'

            db.commit()
            flash(f'Rejected {len(pending_entries)} entries with reason: {reason}')

        return redirect(url_for('officer.approvals'))

    # GET request - show pending submissions
    db = get_db()
    subs = db.query(models.BulkSubmission).filter(
        models.BulkSubmission.status.in_(['PENDING', 'PARTIALLY_APPROVED'])
    ).all()

    # Add entries to each submission
    for sub in subs:
        sub.entries = db.query(models.BulkSubmissionEntry).filter_by(bulk_submission_id=sub.id).all()

    return render_template('approvals.html', subs=subs)


@bp.route('/timelogs', methods=['GET','POST'])
@login_required
def timelogs():
    """Officer view: show and action on pending timelog submissions (approve/reject).
    Approved timelogs will be counted toward student total hours in reports.
    """
    if current_user.role != 'officer':
        abort(403)
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        t_id = request.form.get('id')
        tl = db.query(models.TimeLog).filter_by(id=t_id).first()
        if not tl:
            flash('Timelog not found')
            return redirect(url_for('officer.timelogs'))
        if action == 'approve':
            # This is a regular timelog submission
            # if hours not calculated, try to compute from start/stop
            try:
                if not tl.calculated_hours and tl.start_ts and tl.stop_ts:
                    from datetime import datetime
                    s = datetime.fromisoformat(tl.start_ts)
                    e = datetime.fromisoformat(tl.stop_ts)
                    hrs = round((e - s).total_seconds() / 3600.0, 3)
                    tl.calculated_hours = hrs
            except Exception:
                # leave as-is if parsing fails
                pass
            tl.status = 'APPROVED'
            db.commit()
            flash('Timelog approved')
        elif action == 'reject':
            tl.status = 'REJECTED'
            db.commit()
            flash('Timelog rejected')
        return redirect(url_for('officer.timelogs'))

    pending = db.query(models.TimeLog, models.Event.name.label('event_name')).join(models.Event, models.TimeLog.event_id == models.Event.id).filter(models.TimeLog.status == 'PENDING').all()
    # Convert to objects with event_name attribute for template compatibility
    pending_with_names = []
    for tl, event_name in pending:
        tl.event_name = event_name
        pending_with_names.append(tl)
    return render_template('pending_timelogs.html', timelogs=pending_with_names)


@bp.route('/event_requests', methods=['GET','POST'])
@login_required
def event_requests():
    """Officer view: show and action on pending event join requests (approve/reject).
    Approved requests allow volunteers to join active events.
    """
    if current_user.role != 'officer':
        abort(403)
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        t_id = request.form.get('id')
        tl = db.query(models.TimeLog).filter_by(id=t_id).first()
        if not tl:
            flash('Event request not found')
            return redirect(url_for('officer.event_requests'))
        if action == 'approve':
            # This is an event join request for an active event
            tl.status = 'APPROVED'
            db.commit()
            flash('Volunteer approved to join the event!')
        elif action == 'reject':
            tl.status = 'REJECTED'
            db.commit()
            flash('Volunteer request to join event rejected')
        return redirect(url_for('officer.event_requests'))

    pending = db.query(models.TimeLog, models.Event.name.label('event_name')).join(models.Event, models.TimeLog.event_id == models.Event.id).filter(models.TimeLog.status == 'PENDING_APPROVAL').all()
    # Convert to objects with event_name attribute for template compatibility
    pending_with_names = []
    for tl, event_name in pending:
        tl.event_name = event_name
        pending_with_names.append(tl)
    return render_template('pending_event_requests.html', timelogs=pending_with_names)


@bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    # Allow both officers and club leaders to access reports
    if current_user.role not in ('officer', 'club_leader'):
        abort(403)
    
    db = get_db()
    
    # Get basic stats for dashboard
    total_hours = db.query(func.sum(models.TimeLog.calculated_hours)).filter_by(status='APPROVED').scalar() or 0
    total_volunteers = db.query(func.count(func.distinct(models.TimeLog.student_email))).filter_by(status='APPROVED').scalar() or 0
    total_events = db.query(func.count(func.distinct(models.TimeLog.event_id))).filter_by(status='APPROVED').scalar() or 0
    
    stats = {
        'total_hours': float(total_hours),
        'total_volunteers': total_volunteers,
        'total_events': total_events
    }
    
    # Get club options for dropdown
    club_options = []
    if current_user.role == 'officer':
        # Officers can see all clubs
        clubs = db.query(models.User.club_id).filter(
            models.User.role == 'club_leader',
            models.User.club_id.isnot(None)
        ).distinct().all()
        club_options = [('', 'All Clubs')] + [(club[0], club[0]) for club in clubs if club[0]]
        stats['total_clubs'] = len([c for c in clubs if c[0]])
    else:
        # Club leaders only see their own club
        club_options = [(current_user.club_id, current_user.club_id)] if current_user.club_id else []
    
    # Get event options for dropdown
    event_options = []
    if current_user.role == 'officer':
        # Officers can see all events
        events = db.query(models.Event.id, models.Event.name).all()
        event_options = [('', 'All Events')] + [(str(e.id), f"{e.name} ({e.id})") for e in events]
    else:
        # Club leaders see events associated with their club (events they created or bulk submissions)
        # For now, show all events - this could be refined based on business logic
        events = db.query(models.Event.id, models.Event.name).all()
        event_options = [('', 'All Events')] + [(str(e.id), f"{e.name} ({e.id})") for e in events]
    
    # Handle report generation if POST request
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        if report_type:
            data = generate_report_data(db, report_type)
            return jsonify(data)  # Return JSON data for frontend
    
    return render_template('reports.html', 
                         stats=stats, 
                         club_options=club_options, 
                         event_options=event_options)


@bp.route('/reports/export/csv', methods=['POST'])
@login_required
def export_csv():
    if current_user.role not in ('officer', 'club_leader'):
        abort(403)
    
    db = get_db()
    report_type = request.form.get('report_type')
    if not report_type:
        flash('Report type required')
        return redirect(url_for('officer.reports'))
    
    # Get the data
    result = generate_report_data(db, report_type)
    if 'error' in result:
        flash(result['error'])
        return redirect(url_for('officer.reports'))
    
    # Convert to DataFrame and export CSV
    df = pd.DataFrame(result['data'])
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    
    filename = f"volunteer_report_{report_type}_{result['rtype']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(io.BytesIO(csv_buf.getvalue().encode('utf-8')), 
                    mimetype='text/csv', 
                    as_attachment=True, 
                    download_name=filename)


@bp.route('/reports/export/xlsx', methods=['POST'])
@login_required
def export_xlsx():
    if current_user.role not in ('officer', 'club_leader'):
        abort(403)
    
    db = get_db()
    report_type = request.form.get('report_type')
    if not report_type:
        flash('Report type required')
        return redirect(url_for('officer.reports'))
    
    # Get the data
    result = generate_report_data(db, report_type)
    if 'error' in result:
        flash(result['error'])
        return redirect(url_for('officer.reports'))
    
    # Convert to DataFrame and export XLSX
    df = pd.DataFrame(result['data'])
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)
    xlsx_buf.seek(0)
    
    filename = f"volunteer_report_{report_type}_{result['rtype']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(xlsx_buf, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                    as_attachment=True, 
                    download_name=filename)


def generate_report_data(db, report_type):
    """Generate report data for display and graphs"""
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    student_email = (request.form.get('student_email') or '').strip().lower()
    club_id = request.form.get('club_id')
    event_id = request.form.get('event_id')
    rtype = request.form.get('type') or 'general'

    # Base query for approved timelogs
    query = db.query(models.TimeLog).filter_by(status='APPROVED')
    
    # Apply role-based filtering
    if current_user.role == 'club_leader':
        # Club leaders can only see data related to their club
        # This is a simplified approach - in reality you'd need to link timelogs to clubs
        # For now, we'll allow club leaders to see all data but this should be restricted
        pass  # TODO: Implement proper club-based filtering
    
    # Apply report type filters
    if report_type == 'club' and club_id:
        # Filter by club - this requires linking timelogs to clubs
        # For now, this is a placeholder
        pass  # TODO: Implement club filtering
    
    if report_type == 'event' and event_id:
        query = query.filter(models.TimeLog.event_id == event_id)
    
    if report_type == 'student' and student_email:
        query = query.filter(models.TimeLog.student_email.ilike(f"%{student_email}%"))
    
    # Apply date filters
    if start_date:
        try:
            from datetime import datetime
            sdt = datetime.fromisoformat(start_date)
            query = query.filter(models.TimeLog.start_ts >= sdt.isoformat())
        except Exception:
            pass
    
    if end_date:
        try:
            from datetime import datetime
            edt = datetime.fromisoformat(end_date)
            query = query.filter(models.TimeLog.stop_ts <= edt.isoformat())
        except Exception:
            pass

    timelogs = query.all()
    
    if not timelogs:
        return {'error': 'No approved records found matching your criteria'}
    
    # Convert to DataFrame for processing
    import pandas as pd
    rows = []
    for t in timelogs:
        # Get event name
        event_name = "Unknown Event"
        if t.event_id:
            if t.event_id.startswith('BULK_'):
                bid = t.event_id.replace('BULK_','')
                b = db.query(models.BulkSubmission).filter_by(id=bid).first()
                event_name = b.project_name if b else 'Bulk Submission'
            else:
                event = db.query(models.Event).filter_by(id=t.event_id).first()
                if event:
                    event_name = event.name
        
        rows.append({
            'student_email': t.student_email,
            'event_id': t.event_id,
            'event_name': event_name,
            'calculated_hours': t.calculated_hours or 0,
            'status': t.status,
            'start_ts': t.start_ts,
            'stop_ts': t.stop_ts,
            'marker': t.marker
        })
    
    df = pd.DataFrame(rows)
    
    # Generate different report formats
    if rtype == 'general':
        data = df[['student_email', 'event_name', 'calculated_hours', 'status', 'start_ts', 'stop_ts', 'marker']].to_dict('records')
        chart_df = df
    elif rtype == 'person_summary':
        if report_type == 'student' and not student_email:
            return {'error': 'Student email is required for person_summary reports'}
        summary = df.groupby('student_email').agg({'calculated_hours': 'sum'}).reset_index()
        data = summary.rename(columns={'calculated_hours': 'total_hours'}).to_dict('records')
        chart_df = summary.rename(columns={'calculated_hours': 'total_hours'})
    elif rtype == 'person_detailed':
        if report_type == 'student' and not student_email:
            return {'error': 'Student email is required for person_detailed reports'}
        data = df[['student_email', 'event_name', 'calculated_hours', 'start_ts', 'stop_ts', 'status']].to_dict('records')
        chart_df = df
    else:
        return {'error': 'Unknown report type'}

    # Prepare chart data
    chart_data = prepare_chart_data(chart_df, rtype)
    
    return {
        'data': data,
        'chart_data': chart_data,
        'report_type': report_type,
        'rtype': rtype
    }


def prepare_chart_data(df, rtype):
    """Prepare data for Chart.js visualization"""
    chart_data = {}
    
    if rtype == 'person_summary':
        # Bar chart of top volunteers by hours
        # For person_summary, df is already summarized with 'total_hours' column
        top_volunteers = df.nlargest(10, 'total_hours')
        chart_data = {
            'type': 'bar',
            'labels': top_volunteers['student_email'].tolist(),
            'datasets': [{
                'label': 'Total Hours',
                'data': top_volunteers['total_hours'].tolist(),
                'backgroundColor': 'rgba(11, 79, 108, 0.6)',
                'borderColor': 'rgba(11, 79, 108, 1)',
                'borderWidth': 1
            }]
        }
    elif rtype == 'general':
        # Pie chart of hours by event
        event_hours = df.groupby('event_name')['calculated_hours'].sum().nlargest(10)
        chart_data = {
            'type': 'pie',
            'labels': event_hours.index.tolist(),
            'datasets': [{
                'label': 'Hours by Event',
                'data': event_hours.values.tolist(),
                'backgroundColor': [
                    'rgba(11, 79, 108, 0.8)',
                    'rgba(25, 130, 196, 0.8)',
                    'rgba(38, 166, 154, 0.8)',
                    'rgba(76, 175, 80, 0.8)',
                    'rgba(139, 195, 74, 0.8)',
                    'rgba(205, 220, 57, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(255, 87, 34, 0.8)',
                    'rgba(183, 28, 28, 0.8)'
                ]
            }]
        }
    elif rtype == 'person_detailed':
        # Line chart of hours over time (simplified)
        df['date'] = pd.to_datetime(df['start_ts']).dt.date
        daily_hours = df.groupby('date')['calculated_hours'].sum()
        chart_data = {
            'type': 'line',
            'labels': [str(d) for d in daily_hours.index],
            'datasets': [{
                'label': 'Daily Hours',
                'data': daily_hours.values.tolist(),
                'borderColor': 'rgba(11, 79, 108, 1)',
                'backgroundColor': 'rgba(11, 79, 108, 0.1)',
                'tension': 0.4
            }]
        }
    
    return chart_data


@bp.route('/email_logs')
@login_required
def email_logs():
    if current_user.role != 'officer':
        abort(403)
    db = get_db()
    logs = db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).limit(200).all()
    return render_template('email_logs.html', logs=logs)


@bp.route('/manage_events')
@login_required
def manage_events():
    """Officer view: manage all events created by the officer."""
    if current_user.role != 'officer':
        abort(403)
    db = get_db()
    
    # Get all events created by this officer
    events = db.query(models.Event).filter_by(officer_id=current_user.id).order_by(models.Event.created_at.desc()).all()
    
    # Get volunteer counts for each event
    event_volunteers = {}
    for event in events:
        # Count approved volunteers for this event
        volunteer_count = db.query(models.TimeLog).filter_by(
            event_id=event.id, 
            status='APPROVED'
        ).count()
        event_volunteers[event.id] = volunteer_count
    
    return render_template('manage_events.html', events=events, event_volunteers=event_volunteers, datetime=datetime)


@bp.route('/edit_event/<event_id>', methods=['GET','POST'])
@login_required
def edit_event(event_id):
    """Officer view: edit an existing event."""
    if current_user.role != 'officer':
        abort(403)
    
    db = get_db()
    event = db.query(models.Event).filter_by(id=event_id, officer_id=current_user.id).first()
    if not event:
        flash('Event not found or you do not have permission to edit it.')
        return redirect(url_for('officer.manage_events'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_raw = request.form.get('start')
        end_raw = request.form.get('end')
        location = request.form.get('location')
        description = request.form.get('description')
        volunteer_limit = request.form.get('volunteer_limit')
        
        # Convert volunteer_limit to int if provided
        volunteer_limit_int = None
        if volunteer_limit:
            try:
                volunteer_limit_int = int(volunteer_limit)
                if volunteer_limit_int <= 0:
                    volunteer_limit_int = None
            except ValueError:
                volunteer_limit_int = None
        
        # parse start/end timestamps from datetime-local inputs
        sd = None
        ed = None
        from datetime import datetime
        def _try_parse(s):
            if not s:
                return None
            try:
                # datetime-local typically looks like 'YYYY-MM-DDTHH:MM' or with seconds
                return datetime.fromisoformat(s)
            except Exception:
                try:
                    return datetime.fromisoformat(s.replace('T', ' '))
                except Exception:
                    return None
        sd = _try_parse(start_raw)
        ed = _try_parse(end_raw)

        # validate start exists and end is after start
        if not sd:
            flash('Start date/time is required and must be a valid datetime')
            return render_template('create_event.html', 
                                 name=name, start=start_raw, end=end_raw, 
                                 location=location, description=description, 
                                 volunteer_limit=volunteer_limit, editing=True, event=event)
        if ed and ed < sd:
            flash('End date/time must be after start date/time')
            return render_template('create_event.html', 
                                 name=name, start=start_raw, end=end_raw, 
                                 location=location, description=description, 
                                 volunteer_limit=volunteer_limit, editing=True, event=event)

        # Update event
        event.name = name
        event.start_ts = sd
        event.end_ts = ed
        event.location = location
        event.description = description
        event.volunteer_limit = volunteer_limit_int
        
        db.commit()
        flash('Event updated successfully!')
        return redirect(url_for('officer.manage_events'))

    # Format timestamps for form
    start_formatted = event.start_ts.strftime('%Y-%m-%dT%H:%M') if event.start_ts else ''
    end_formatted = event.end_ts.strftime('%Y-%m-%dT%H:%M') if event.end_ts else ''
    
    return render_template('create_event.html', 
                         name=event.name, start=start_formatted, end=end_formatted,
                         location=event.location, description=event.description,
                         volunteer_limit=event.volunteer_limit, editing=True, event=event)


@bp.route('/delete_event/<event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """Officer view: delete an event."""
    if current_user.role != 'officer':
        abort(403)
    
    db = get_db()
    event = db.query(models.Event).filter_by(id=event_id, officer_id=current_user.id).first()
    if not event:
        flash('Event not found or you do not have permission to delete it.')
        return redirect(url_for('officer.manage_events'))
    
    # Check if there are any approved volunteers for this event
    approved_count = db.query(models.TimeLog).filter_by(event_id=event_id, status='APPROVED').count()
    if approved_count > 0:
        flash(f'Cannot delete event with {approved_count} approved volunteer(s). Please remove all volunteers first.')
        return redirect(url_for('officer.manage_events'))
    
    # Delete all timelogs associated with this event (including pending ones)
    db.query(models.TimeLog).filter_by(event_id=event_id).delete()
    
    # Delete the event
    db.delete(event)
    db.commit()
    
    flash('Event deleted successfully!')
    return redirect(url_for('officer.manage_events'))


@bp.route('/event_volunteers/<event_id>', methods=['GET','POST'])
@login_required
def view_event_volunteers(event_id):
    """Officer view: manage volunteers signed up for a specific event."""
    if current_user.role != 'officer':
        abort(403)
    
    db = get_db()
    event = db.query(models.Event).filter_by(id=event_id, officer_id=current_user.id).first()
    if not event:
        flash('Event not found or you do not have permission to view it.')
        return redirect(url_for('officer.manage_events'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        volunteer_email = request.form.get('volunteer_email')
        
        if action == 'approve':
            # Approve the volunteer signup
            timelog = db.query(models.TimeLog).filter_by(
                event_id=event_id, 
                student_email=volunteer_email
            ).first()
            
            if timelog:
                timelog.status = 'APPROVED'
                db.commit()
                flash(f'Approved {volunteer_email} for the event.', 'success')
            else:
                flash('Volunteer not found for this event.', 'error')
        
        elif action == 'reject':
            # Reject and remove the volunteer signup
            timelog = db.query(models.TimeLog).filter_by(
                event_id=event_id, 
                student_email=volunteer_email
            ).first()
            
            if timelog:
                db.delete(timelog)
                db.commit()
                flash(f'Rejected signup from {volunteer_email}.', 'success')
            else:
                flash('Volunteer not found for this event.', 'error')
        
        elif action == 'remove':
            # Find and remove the volunteer from this event
            timelog = db.query(models.TimeLog).filter_by(
                event_id=event_id, 
                student_email=volunteer_email
            ).first()
            
            if timelog:
                db.delete(timelog)
                db.commit()
                flash(f'Removed {volunteer_email} from the event.', 'success')
            else:
                flash('Volunteer not found for this event.', 'error')
        
        return redirect(url_for('officer.view_event_volunteers', event_id=event_id))
    
    # Get all volunteers for this event
    volunteers = db.query(models.TimeLog, models.User.name.label('volunteer_name')).join(
        models.User, models.TimeLog.student_email == models.User.email, isouter=True
    ).filter(
        models.TimeLog.event_id == event_id
    ).order_by(models.TimeLog.status, models.TimeLog.student_email).all()
    
    # Convert to objects with volunteer_name attribute
    volunteer_list = []
    for tl, volunteer_name in volunteers:
        tl.volunteer_name = volunteer_name or tl.student_email
        volunteer_list.append(tl)
    
    return render_template('event_volunteers.html', event=event, volunteers=volunteer_list)
