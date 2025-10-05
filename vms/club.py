from flask import Blueprint, render_template, request, flash, current_app, abort
from flask_login import login_required, current_user
import json

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
        hours_data_raw = request.form.get('hours_data')
        try:
            hours_data = json.loads(hours_data_raw)
            if not isinstance(hours_data, list):
                raise ValueError('Must be a list')
            clean = []
            for it in hours_data:
                email = (it.get('email') or '').strip().lower()
                h = float(it.get('hours') or 0)
                if not models.is_valid_email(email):
                    raise ValueError('Invalid email: ' + str(email))
                clean.append({'email': email, 'hours': h})
        except Exception as e:
            flash('Invalid hours data: ' + str(e))
            return render_template('submit_hours.html')
        b_id = 'b_' + str(__import__('uuid').uuid4())
        import json as _json
        db = get_db()
        sub = models.BulkSubmission(id=b_id, club_leader_id=current_user.id, project_name=project_name, date_range=date_range, description=description, status='PENDING', hours_data=_json.dumps(clean))
        db.add(sub)
        db.commit()
        flash('Bulk submission created and pending officer approval')
        return render_template('submit_hours.html')
