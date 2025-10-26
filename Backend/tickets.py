from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from .models import Ticket, TicketResponse, TicketAttachment, User, gen_id
from .db import get_db
from .email import send_email

bp = Blueprint('tickets', __name__, url_prefix='/tickets')

# File upload configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_dir():
    """Get the upload directory path"""
    upload_dir = os.path.join(current_app.root_path, 'uploads', 'tickets')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def save_attachment(file, ticket_id, response_id=None):
    """Save uploaded file and create attachment record"""
    if not file or not allowed_file(file.filename):
        raise ValueError("Invalid file type")

    if file.content_length > MAX_FILE_SIZE:
        raise ValueError("File too large (max 10MB)")

    # Generate secure filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{gen_id('')}_{filename}"

    # Save file
    upload_dir = get_upload_dir()
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    # Create attachment record
    attachment = TicketAttachment(
        id=gen_id('ta_'),
        ticket_id=ticket_id,
        response_id=response_id,
        uploader_id=current_user.id,
        filename=unique_filename,
        original_filename=filename,
        file_size=os.path.getsize(file_path),
        mime_type=file.mimetype or 'application/octet-stream',
        file_path=unique_filename
    )

    return attachment


@bp.route('/')
@login_required
def index():
    """List tickets based on user role"""
    db = get_db()

    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    priority_filter = request.args.get('priority', '').strip()

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    # Base query
    query = db.query(Ticket)

    # Apply role-based filtering
    if current_user.role == 'officer':
        # Officers see all tickets
        pass
    else:
        # Regular users see only their own tickets
        query = query.filter_by(submitter_id=current_user.id)

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )

    # Apply status filter
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Apply category filter
    if category_filter:
        query = query.filter_by(category=category_filter)

    # Apply priority filter
    if priority_filter:
        query = query.filter_by(priority=priority_filter)

    # Get total count for pagination
    total_tickets = query.count()

    # Order by most recent first and paginate
    tickets = query.order_by(desc(Ticket.updated_at)).offset((page - 1) * per_page).limit(per_page).all()

    # Calculate pagination info
    total_pages = (total_tickets + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    start_ticket = (page - 1) * per_page + 1
    end_ticket = min(page * per_page, total_tickets)

    pagination = {
        'page': page,
        'per_page': per_page,
        'total_tickets': total_tickets,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev,
        'next_page': page + 1 if has_next else None,
        'prev_page': page - 1 if has_prev else None,
        'start_ticket': start_ticket,
        'end_ticket': end_ticket,
        'pages': list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
    }

    # Get officers list for bulk assignment (officers only)
    officers = []
    if current_user.role == 'officer':
        officers = db.query(User).filter_by(role='officer').order_by(User.name).all()

    return render_template('tickets/index.html', tickets=tickets, pagination=pagination, officers=officers)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new ticket"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'general')
        priority = request.form.get('priority', 'normal')

        # Validation
        if not title or len(title) < 5:
            flash('Title must be at least 5 characters long.', 'error')
            return redirect(url_for('tickets.create'))

        if not description or len(description) < 10:
            flash('Description must be at least 10 characters long.', 'error')
            return redirect(url_for('tickets.create'))

        if category not in ['suggestion', 'problem', 'bug', 'feature_request', 'general']:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('tickets.create'))

        if priority not in ['low', 'normal', 'high', 'urgent']:
            flash('Invalid priority selected.', 'error')
            return redirect(url_for('tickets.create'))

        # Create ticket
        db = get_db()
        ticket = Ticket(
            id=gen_id('tk_'),
            submitter_id=current_user.id,
            title=title,
            description=description,
            category=category,
            priority=priority
        )

        db.add(ticket)
        db.commit()

        # Handle file attachments
        attachments = request.files.getlist('attachments')
        for file in attachments:
            if file and file.filename and allowed_file(file.filename):
                try:
                    attachment = save_attachment(file, ticket.id)
                    db.add(attachment)
                except ValueError as e:
                    flash(f'Failed to upload {file.filename}: {str(e)}', 'error')
                except Exception as e:
                    flash(f'Failed to upload {file.filename}.', 'error')
                    current_app.logger.error(f"Attachment upload failed for {file.filename}: {e}")

        db.commit()

        flash('Your ticket has been submitted successfully. An officer will review it soon.', 'success')

        # Send email notification to officers
        notify_ticket_created(ticket)

        return redirect(url_for('tickets.view', ticket_id=ticket.id))

    return render_template('tickets/create.html')


@bp.route('/<ticket_id>')
@login_required
def view(ticket_id):
    """View a specific ticket and its responses"""
    db = get_db()
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        abort(404)

    # Check permissions
    if current_user.role != 'officer' and ticket.submitter_id != current_user.id:
        abort(403)

    # Get responses
    responses = db.query(TicketResponse).filter_by(ticket_id=ticket_id).order_by(TicketResponse.created_at).all()

    # Get user info for responses
    response_users = {}
    for response in responses:
        if response.responder_id not in response_users:
            user = db.query(User).filter_by(id=response.responder_id).first()
            response_users[response.responder_id] = user.name if user else 'Unknown'

    return render_template('tickets/view.html',
                         ticket=ticket,
                         responses=responses,
                         response_users=response_users)


@bp.route('/<ticket_id>/respond', methods=['POST'])
@login_required
def respond(ticket_id):
    """Add a response to a ticket"""
    if current_user.role != 'officer':
        abort(403)

    db = get_db()
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        abort(404)

    response_text = request.form.get('response', '').strip()
    is_internal = request.form.get('is_internal') == '1'

    if not response_text or len(response_text) < 5:
        flash('Response must be at least 5 characters long.', 'error')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

    # Create response
    response = TicketResponse(
        id=gen_id('tr_'),
        ticket_id=ticket_id,
        responder_id=current_user.id,
        response_text=response_text,
        is_internal=is_internal
    )

    # Update ticket status if provided
    new_status = request.form.get('status')
    if new_status in ['open', 'in_progress', 'resolved', 'closed']:
        ticket.status = new_status

    db.add(response)
    db.commit()

    flash('Response added successfully.', 'success')

    # Send email notification
    notify_ticket_response(ticket, response)

    return redirect(url_for('tickets.view', ticket_id=ticket_id))


@bp.route('/<ticket_id>/assign', methods=['POST'])
@login_required
def assign(ticket_id):
    """Assign ticket to an officer"""
    if current_user.role != 'officer':
        abort(403)

    db = get_db()
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        abort(404)

    officer_id = request.form.get('officer_id')

    if officer_id:
        officer = db.query(User).filter_by(id=officer_id, role='officer').first()
        if not officer:
            flash('Invalid officer selected.', 'error')
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        ticket.assigned_officer_id = officer_id
    else:
        ticket.assigned_officer_id = None

    db.commit()
    flash('Ticket assignment updated.', 'success')

    # Send email notification
    notify_ticket_assigned(ticket)

    return redirect(url_for('tickets.view', ticket_id=ticket_id))


@bp.route('/<ticket_id>/status', methods=['POST'])
@login_required
def update_status(ticket_id):
    """Update ticket status"""
    if current_user.role != 'officer':
        abort(403)

    db = get_db()
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        abort(404)

    new_status = request.form.get('status')
    if new_status not in ['open', 'in_progress', 'resolved', 'closed']:
        flash('Invalid status.', 'error')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

    old_status = ticket.status
    ticket.status = new_status
    db.commit()

    flash(f'Ticket status updated to {ticket.status_display}.', 'success')

    # Send email notification if status changed
    notify_ticket_status_changed(ticket, old_status)

    return redirect(url_for('tickets.view', ticket_id=ticket_id))


# Email notification functions
def send_ticket_notification(ticket, action, recipients=None, response=None):
    """Send email notification for ticket events"""
    try:
        if not recipients:
            # Default recipients based on action
            if action == 'created':
                # Notify all officers
                db = get_db()
                officers = db.query(User).filter_by(role='officer').all()
                recipients = [officer.email for officer in officers]
            elif action in ['responded', 'status_changed', 'assigned']:
                # Notify ticket submitter
                recipients = [ticket.submitter.email] if ticket.submitter else []

        if not recipients:
            return

        subject = f"Ticket #{ticket.id.split('_')[1]} - {action.replace('_', ' ').title()}"

        # Create email body
        body = f"""
Ticket: {ticket.title}
ID: {ticket.id.split('_')[1]}
Category: {ticket.category_display}
Priority: {ticket.priority_display}
Status: {ticket.status_display}
Submitted by: {ticket.submitter.name if ticket.submitter else 'Unknown'}

{ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}

View ticket: {url_for('tickets.view', ticket_id=ticket.id, _external=True)}
"""

        if response:
            body += f"\n\nLatest Response from {response.author.name}:\n{response.response_text[:200]}{'...' if len(response.response_text) > 200 else ''}"

        send_email(
            subject=subject,
            body=body,
            recipients=recipients,
            async_send=True
        )

    except Exception as e:
        # Log error but don't fail the operation
        try:
            current_app.logger.error(f"Failed to send ticket notification: {e}")
        except Exception:
            pass


def notify_ticket_created(ticket):
    """Send notification when ticket is created"""
    send_ticket_notification(ticket, 'created')


def notify_ticket_response(ticket, response):
    """Send notification when ticket gets a response"""
    send_ticket_notification(ticket, 'responded', response=response)


def notify_ticket_status_changed(ticket, old_status):
    """Send notification when ticket status changes"""
    if ticket.status != old_status:
        send_ticket_notification(ticket, 'status_changed')


def notify_ticket_assigned(ticket):
    """Send notification when ticket is assigned"""
    if ticket.assigned_officer:
        send_ticket_notification(ticket, 'assigned', recipients=[ticket.assigned_officer.email])


@bp.route('/attachment/<attachment_id>')
@login_required
def download_attachment(attachment_id):
    """Download a ticket attachment"""
    db = get_db()
    attachment = db.query(TicketAttachment).filter_by(id=attachment_id).first()

    if not attachment:
        abort(404)

    # Check permissions
    ticket = attachment.ticket
    if current_user.role != 'officer' and ticket.submitter_id != current_user.id:
        abort(403)

    upload_dir = get_upload_dir()
    return send_from_directory(upload_dir, attachment.file_path,
                             download_name=attachment.original_filename,
                             as_attachment=True)


@bp.route('/<ticket_id>/attach', methods=['POST'])
@login_required
def upload_attachment(ticket_id):
    """Upload attachment to a ticket"""
    db = get_db()
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        abort(404)

    # Check permissions
    if current_user.role != 'officer' and ticket.submitter_id != current_user.id:
        abort(403)

    file = request.files.get('attachment')
    if not file or file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

    try:
        attachment = save_attachment(file, ticket_id)
        db.add(attachment)
        db.commit()

        flash('Attachment uploaded successfully.', 'success')

    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('Failed to upload attachment.', 'error')
        current_app.logger.error(f"Attachment upload failed: {e}")

    return redirect(url_for('tickets.view', ticket_id=ticket_id))


@bp.route('/bulk_update', methods=['POST'])
@login_required
def bulk_update():
    """Handle bulk operations on tickets (officer only)"""
    if current_user.role != 'officer':
        abort(403)

    ticket_ids = request.form.getlist('ticket_ids')
    bulk_action = request.form.get('bulk_action')
    assign_to = request.form.get('assign_to')

    if not ticket_ids:
        flash('No tickets selected.', 'error')
        return redirect(url_for('tickets.index'))

    if not bulk_action:
        flash('No action selected.', 'error')
        return redirect(url_for('tickets.index'))

    db = get_db()
    tickets = db.query(Ticket).filter(Ticket.id.in_(ticket_ids)).all()

    if not tickets:
        flash('No valid tickets found.', 'error')
        return redirect(url_for('tickets.index'))

    updated_count = 0

    try:
        if bulk_action.startswith('status_'):
            new_status = bulk_action.replace('status_', '')
            valid_statuses = ['open', 'in_progress', 'resolved']
            if new_status not in valid_statuses:
                flash('Invalid status.', 'error')
                return redirect(url_for('tickets.index'))

            for ticket in tickets:
                ticket.status = new_status
                ticket.updated_at = datetime.utcnow()
                updated_count += 1

        elif bulk_action == 'assign_me':
            for ticket in tickets:
                ticket.assigned_officer_id = current_user.id
                ticket.updated_at = datetime.utcnow()
                updated_count += 1

        elif bulk_action == 'assign_officer':
            if not assign_to:
                flash('No officer selected for assignment.', 'error')
                return redirect(url_for('tickets.index'))

            officer = db.query(User).filter(User.id == assign_to, User.role == 'officer').first()
            if not officer:
                flash('Invalid officer selected.', 'error')
                return redirect(url_for('tickets.index'))

            for ticket in tickets:
                ticket.assigned_officer_id = assign_to
                ticket.updated_at = datetime.utcnow()
                updated_count += 1

        elif bulk_action == 'unassign':
            for ticket in tickets:
                ticket.assigned_officer_id = None
                ticket.updated_at = datetime.utcnow()
                updated_count += 1

        elif bulk_action == 'delete':
            # Delete associated responses and attachments first
            for ticket in tickets:
                # Delete attachments
                attachments = db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket.id).all()
                for attachment in attachments:
                    try:
                        file_path = os.path.join(get_upload_dir(), attachment.filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        current_app.logger.error(f"Failed to delete attachment file {attachment.filename}: {e}")

                # Delete responses and attachments
                db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket.id).delete()
                db.query(TicketResponse).filter(TicketResponse.ticket_id == ticket.id).delete()

            # Delete tickets
            for ticket in tickets:
                db.delete(ticket)
                updated_count += 1

        else:
            flash('Invalid action.', 'error')
            return redirect(url_for('tickets.index'))

        db.commit()

        # Send email notifications for status changes
        if bulk_action.startswith('status_'):
            for ticket in tickets:
                try:
                    send_ticket_notification(ticket, f"Status updated to {new_status.replace('_', ' ')}")
                except Exception as e:
                    current_app.logger.error(f"Failed to send notification for ticket {ticket.id}: {e}")

        action_messages = {
            'status_resolved': f'Marked {updated_count} ticket(s) as resolved.',
            'status_in_progress': f'Marked {updated_count} ticket(s) as in progress.',
            'status_open': f'Marked {updated_count} ticket(s) as open.',
            'assign_me': f'Assigned {updated_count} ticket(s) to yourself.',
            'assign_officer': f'Assigned {updated_count} ticket(s) to officer.',
            'unassign': f'Unassigned {updated_count} ticket(s).',
            'delete': f'Deleted {updated_count} ticket(s).'
        }

        flash(action_messages.get(bulk_action, f'Updated {updated_count} ticket(s).'), 'success')

    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Bulk update failed: {e}")
        flash('Failed to update tickets.', 'error')

    return redirect(url_for('tickets.index'))