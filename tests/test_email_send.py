from vms import create_app
from vms.db import get_db
from vms import models

class DummySMTP:
    def __init__(self, *a, **kw):
        pass
    def ehlo(self):
        pass
    def send_message(self, msg):
        return True
    def quit(self):
        pass

class FailingSMTP(DummySMTP):
    def send_message(self, msg):
        raise Exception('fail')

def run_tests_manual():
    app = create_app()
    with app.app_context():
        # success path
        models.set_setting('SMTP_HOST', '127.0.0.1')
        models.set_setting('SMTP_PORT', '1025')
        import vms.email as email_mod
        import smtplib
        orig = smtplib.SMTP
        try:
            smtplib.SMTP = lambda *a, **k: DummySMTP()
            email_mod.send_email('sub', 'body', ['ok@example.local'], async_send=False)
            db = get_db()
            last = db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).first()
            print('SUCCESS last.status=', last.status)
        finally:
            smtplib.SMTP = orig

        # failure path
        try:
            # clear SMTP cache so fallback recreates the client
            try:
                from vms.email import clear_smtp_cache
                clear_smtp_cache()
            except Exception:
                pass
            smtplib.SMTP = lambda *a, **k: FailingSMTP()
            email_mod.send_email('sub', 'body', ['bad@example.local'], async_send=False)
            db = get_db()
            last = db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).first()
            print('FAIL last.status=', last.status)
        finally:
            smtplib.SMTP = orig
