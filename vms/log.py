from flask import Blueprint, render_template, request, current_app
from datetime import datetime, timedelta
import jwt

from .models import next_timelog_id
from .db import get_db

bp = Blueprint('log', __name__)


def make_logging_jwt(event_id, volunteer_email, hours=24):
    payload = {
        'event_id': event_id,
        'volunteer_email': volunteer_email,
        'exp': datetime.utcnow() + timedelta(hours=hours),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, current_app.config.get('JWT_SECRET','jwt-secret'), algorithm=current_app.config.get('JWT_ALGORITHM','HS256'))
    return token


def decode_logging_jwt(token):
    try:
        payload = jwt.decode(token, current_app.config.get('JWT_SECRET','jwt-secret'), algorithms=[current_app.config.get('JWT_ALGORITHM','HS256')])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Link has expired.'
    except jwt.InvalidTokenError:
        return None, 'Invalid link.'


@bp.route('/log/<jwt_token>', methods=['GET','POST'])
def log_via_jwt(jwt_token):
    payload, error = decode_logging_jwt(jwt_token)
    if error:
        return render_template('log.html', error=error)
    db = get_db()
    event = db.query(__import__('vms.models', fromlist=['Event']).Event).filter_by(id=payload.get('event_id')).first()
    if not event:
        return render_template('log.html', error='Event not found')
    volunteer_email = payload.get('volunteer_email')
    # find open timelog
    open_tl = db.query(__import__('vms.models', fromlist=['TimeLog']).TimeLog).filter_by(event_id=event.id, student_email=volunteer_email, stop_ts=None).first()
    message = None
    if request.method == 'POST':
        action = request.form.get('action')
        now = datetime.utcnow()
        if action == 'start' and not open_tl:
            t_id = 't_' + str(__import__('uuid').uuid4())
            tl = __import__('vms.models', fromlist=['TimeLog']).TimeLog(id=t_id, student_email=volunteer_email, event_id=event.id, start_ts=now.isoformat(), stop_ts=None, calculated_hours=None, status='PENDING')
            db.add(tl)
            db.commit()
            message = f'Clocked in at {now.strftime("%Y-%m-%d %H:%M:%S UTC")}'
            open_tl = db.query(__import__('vms.models', fromlist=['TimeLog']).TimeLog).filter_by(event_id=event.id, student_email=volunteer_email, stop_ts=None).first()
        elif action == 'stop' and open_tl:
            open_tl.stop_ts = datetime.utcnow().isoformat()
            try:
                start = datetime.fromisoformat(open_tl.start_ts)
                stop = datetime.fromisoformat(open_tl.stop_ts)
                delta = stop - start
                hours = delta.total_seconds() / 3600.0
                open_tl.calculated_hours = round(hours, 3)
            except Exception:
                open_tl.calculated_hours = None
            open_tl.status = 'PENDING'
            db.commit()
            message = f'Clocked out at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}, hours={open_tl.get("calculated_hours") if hasattr(open_tl, "get") else getattr(open_tl, "calculated_hours", None)}'
        else:
            message = 'Invalid action or no open session.'
    start_display = None
    open_flag = False
    if open_tl:
        open_flag = True
        try:
            start_display = datetime.fromisoformat(open_tl.start_ts).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            start_display = open_tl.start_ts
    return render_template('log.html', error=None, event=event, volunteer_email=volunteer_email, open=open_flag, start_display=start_display, message=message)
