from flask import Blueprint, render_template, request, flash, url_for, send_file, current_app, redirect, abort
from flask_login import login_required, current_user
import io
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage

from . import models
from .db import get_db
from flask import render_template

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
        date = request.form.get('date')
        location = request.form.get('location')
        description = request.form.get('description')
        file = request.files.get('file')
        if not file:
            flash('File required')
            return render_template('create_event.html', links=None)
        # create event
        event_id = models.Event
        # for now keep generating IDs on the Python side
        import uuid
        eid = 'e_' + str(uuid.uuid4())
        db = get_db()
        ev = models.Event(id=eid, officer_id=current_user.id, name=name, date=date, location=location, description=description)
        db.add(ev)
        db.commit()

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
            return render_template('create_event.html', links=None)
        email_col = 'Email' if 'Email' in df.columns else ('email' if 'email' in df.columns else None)
        if not email_col:
            flash("File must contain 'Email' column")
            return render_template('create_event.html', links=None)
        df['email_norm'] = df[email_col].astype(str).str.strip().str.lower()
        df = df[df['email_norm'].apply(models.is_valid_email)]
        df = df.drop_duplicates(subset=['email_norm'])
        links = []
        from .log import make_logging_jwt
        email_map = {}
        for e in df['email_norm'].tolist():
            token = make_logging_jwt(eid, e, current_app.config.get('JWT_EXP_HOURS',24))
            link = url_for('log.log_via_jwt', jwt_token=token, _external=True)
            links.append(link)
            email_map[e] = link
        # attempt to send emails via the configured Mail subsystem (if initialized)
        sent = 0
        failed = 0
        try:
            from .email import send_email
            subj = f"Logging link for event: {name}"
            default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            for recipient, lnk in email_map.items():
                body = f"Dear volunteer,\n\nYou have been invited to log volunteer hours for the event '{name}'. Use the link below to start/stop your session:\n\n{lnk}\n\nThis link expires in {current_app.config.get('JWT_EXP_HOURS',24)} hours.\n\nThank you,\nAUIB VMS"
                try:
                    send_email(subj, body, recipient, sender=default_sender, async_send=True)
                    sent += 1
                except Exception:
                    current_app.logger.exception('Failed to queue email to %s', recipient)
                    failed += 1
        except Exception:
            current_app.logger.info('Mail subsystem not available; skipping auto-email send')

        flash(f'Event created with {len(links)} unique valid emails — emailed: {sent}, failed: {failed}')
    return render_template('create_event.html', links=links)


@bp.route('/approvals', methods=['GET','POST'])
@login_required
def approvals():
    if current_user.role != 'officer':
        abort(403)
    if request.method == 'POST':
        action = request.form.get('action')
        b_id = request.form.get('id')
        db = get_db()
        sub = db.query(models.BulkSubmission).filter_by(id=b_id).first()
        if not sub:
            flash('Submission not found')
            return redirect(url_for('officer.approvals'))
        if action == 'approve':
            # expand hours_data
            import json
            hours = json.loads(sub.hours_data)
            for h in hours:
                t_id = 't_' + str(__import__('uuid').uuid4())
                tl = models.TimeLog(id=t_id, student_email=h['email'], event_id=f'BULK_{sub.id}', start_ts=None, stop_ts=None, calculated_hours=h['hours'], status='APPROVED', marker='BULK')
                db.add(tl)
            sub.status = 'APPROVED'
            db.commit()
            flash('Submission approved and hours recorded')
        elif action == 'reject':
            reason = request.form.get('reason')
            if not reason:
                flash('Rejection reason required')
                return redirect(url_for('officer.approvals'))
            sub.status = 'REJECTED'
            sub.rejection_reason = reason
            db.commit()
            flash('Submission rejected')
        return redirect(url_for('officer.approvals'))
    db = get_db()
    subs = db.query(models.BulkSubmission).filter_by(status='PENDING').all()
    return render_template('approvals.html', subs=subs)


@bp.route('/timelogs', methods=['GET','POST'])
@login_required
def timelogs():
    """Officer view: show and action on pending timelogs (approve/reject).
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

    pending = db.query(models.TimeLog).filter_by(status='PENDING').all()
    return render_template('pending_timelogs.html', timelogs=pending)


@bp.route('/reports')
@login_required
def reports():
    if current_user.role != 'officer':
        abort(403)
    # reuse logic from previous single-file app
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    student_email = (request.args.get('student_email') or '').strip().lower()
    club_id = request.args.get('club_id')
    rtype = request.args.get('type') or 'general'

    db = get_db()
    rows = []
    for t in db.query(models.TimeLog).filter_by(status='APPROVED').all():
        rows.append({
            'student_email': t.student_email,
            'event_id': t.event_id,
            'calculated_hours': t.calculated_hours,
            'status': t.status,
            'start_ts': t.start_ts,
            'stop_ts': t.stop_ts,
            'marker': t.marker
        })
    import pandas as pd
    df = pd.DataFrame(rows)
    if df.empty:
        flash('No approved records to report')
        return render_template('reports.html')
    df['student_email'] = df['student_email'].str.lower()
    if student_email:
        df = df[df['student_email'] == student_email]

    def in_range(ts):
        if not ts:
            return False
        try:
            d = datetime.fromisoformat(ts)
        except Exception:
            return False
        if start_date:
            try:
                sd = datetime.fromisoformat(start_date)
                if d < sd:
                    return False
            except Exception:
                pass
        if end_date:
            try:
                ed = datetime.fromisoformat(end_date)
                if d > ed:
                    return False
            except Exception:
                pass
        return True

    df['in_range'] = df['start_ts'].apply(lambda x: in_range(x))
    df = df[df['in_range']]

    def event_name(eid):
        if eid.startswith('BULK_'):
            bid = eid.replace('BULK_','')
            b = db.query(models.BulkSubmission).filter_by(id=bid).first()
            return b.project_name if b else 'Bulk Submission'
        ev = db.query(models.Event).filter_by(id=eid).first()
        return ev.name if ev else 'Event/Unknown'

    df['event_name'] = df['event_id'].apply(lambda x: event_name(x))

    if rtype == 'general':
        out = df[['student_email','event_id','event_name','calculated_hours','status','start_ts','stop_ts','marker']].copy()
    elif rtype == 'person_summary':
        if not student_email:
            flash('student_email is required for person_summary')
            return render_template('reports.html')
        total = df['calculated_hours'].fillna(0).sum()
        out = pd.DataFrame([{'student_email': student_email, 'total_hours': total}])
    elif rtype == 'person_detailed':
        if not student_email:
            flash('student_email is required for person_detailed')
            return render_template('reports.html')
        out = df[['student_email','event_name','calculated_hours','start_ts','stop_ts','status']].copy()
    else:
        flash('Unknown report type')
        return render_template('reports.html')

    csv_buf = io.StringIO()
    out.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    return send_file(io.BytesIO(csv_buf.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='report.csv')


@bp.route('/email_logs')
@login_required
def email_logs():
    if current_user.role != 'officer':
        abort(403)
    db = get_db()
    logs = db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).limit(200).all()
    return render_template('email_logs.html', logs=logs)
