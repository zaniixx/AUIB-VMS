from flask import current_app, render_template
import threading
import time
import smtplib
from email.message import EmailMessage

try:
    from mailman import Mail
    mail = Mail()
except Exception:
    mail = None


def init_mail(app):
    if mail is None:
        # use the passed-in app's logger (don't rely on current_app)
        try:
            app.logger.info('Mail subsystem not available (mailman not installed)')
        except Exception:
            pass
        return
    mail.init_app(app)


# simple SMTP client cache keyed by tuple(host,port,user,use_tls,use_ssl)
_smtp_cache = {'client': None, 'cfg': None, 'ts': 0}
_cache_ttl = 30  # seconds


def clear_smtp_cache():
    """Clear cached SMTP client so next send re-reads settings.

    Call this after admin updates SMTP settings to ensure new values
    are picked up without restarting the app.
    """
    global _smtp_cache
    client = _smtp_cache.get('client')
    if client:
        try:
            client.quit()
        except Exception:
            try:
                client.close()
            except Exception:
                pass
    _smtp_cache = {'client': None, 'cfg': None, 'ts': 0}


def send_email(subject, body, recipients, html=None, sender=None, async_send=True, event_id=None):
    """Send an email. Uses Flask-Mailman if available, otherwise falls back to smtplib.

    This function spawns a background thread when async_send=True to avoid blocking the request.
    Errors are logged via the captured app.logger.
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    # capture the active app object and config so the background thread doesn't need a Flask context
    app = current_app._get_current_object()
    sender = sender or app.config.get('MAIL_DEFAULT_SENDER')

    # render HTML if template provided (render now while we have the context)
    try:
        if html is None:
            html = app.jinja_env.get_template('email_link.html').render(
                link=recipients[0] if recipients else '',
                event_name=app.config.get('LAST_EVENT_NAME', 'Event'),
                expires_desc=f"{app.config.get('JWT_EXP_HOURS', 24)} hours",
            )
    except Exception:
        html = None

    def _send():
        # record queued log if DB available
        try:
            from . import models
            for r in recipients:
                try:
                    models.record_email_log(r, subject, body, status='QUEUED', event_id=event_id)
                except Exception:
                    try:
                        app.logger.debug('Could not record queued email log for %s', r)
                    except Exception:
                        pass
        except Exception:
            pass

        # If Flask-Mailman is available and initialized, use it. Otherwise fallback to direct SMTP.
        if mail is not None:
            try:
                mail.send_message(subject, body, sender, recipients, html=html)
                try:
                    app.logger.debug('Email queued/sent to %s', recipients)
                except Exception:
                    pass
                # update logs to SENT
                try:
                    from . import models
                    for r in recipients:
                        try:
                            models.record_email_log(r, subject, body, status='SENT', event_id=event_id)
                        except Exception:
                            try:
                                app.logger.debug('Could not record sent email log for %s', r)
                            except Exception:
                                pass
                except Exception:
                    pass
                return
            except Exception as e:
                try:
                    app.logger.exception('Mailman send failed, falling back to SMTP: %s', e)
                except Exception:
                    pass

        # Fallback: use smtplib with settings loaded from DB or app config
        try:
            from . import models
            host = models.get_setting('SMTP_HOST') or app.config.get('MAIL_SERVER') or '127.0.0.1'
            port = int(models.get_setting('SMTP_PORT') or app.config.get('MAIL_PORT') or 25)
            user = models.get_setting('SMTP_USER') or app.config.get('MAIL_USERNAME')
            pwd = models.get_setting('SMTP_PASS') or app.config.get('MAIL_PASSWORD')
            use_tls = (models.get_setting('SMTP_USE_TLS') == '1') or bool(app.config.get('MAIL_USE_TLS'))
            use_ssl = (models.get_setting('SMTP_USE_SSL') == '1') or bool(app.config.get('MAIL_USE_SSL'))
        except Exception:
            host, port, user, pwd, use_tls, use_ssl = ('127.0.0.1', 25, None, None, False, False)

        cfg_key = (host, port, user, use_tls, use_ssl)
        client = None
        now = time.time()
        try:
            if _smtp_cache['cfg'] == cfg_key and (now - _smtp_cache['ts']) < _cache_ttl and _smtp_cache['client']:
                client = _smtp_cache['client']
            else:
                # create new connection
                if use_ssl:
                    client = smtplib.SMTP_SSL(host, port, timeout=10)
                else:
                    client = smtplib.SMTP(host, port, timeout=10)
                client.ehlo()
                if use_tls and not use_ssl:
                    client.starttls()
                    client.ehlo()
                if user and pwd:
                    client.login(user, pwd)
                _smtp_cache['client'] = client
                _smtp_cache['cfg'] = cfg_key
                _smtp_cache['ts'] = now
        except Exception as e:
            try:
                app.logger.exception('Failed to create SMTP connection: %s', e)
            except Exception:
                pass
            client = None

        if client is None:
            try:
                app.logger.info('No SMTP client available; aborting send')
            except Exception:
                pass
            try:
                from . import models
                for r in recipients:
                    try:
                        models.record_email_log(r, subject, body, status='FAILED', error='No SMTP client', event_id=event_id)
                    except Exception:
                        pass
            except Exception:
                pass
            return

        # build message
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender or (user or app.config.get('MAIL_DEFAULT_SENDER') or 'no-reply@example.local')
            msg['To'] = ', '.join(recipients)
            if html:
                msg.set_content(body)
                msg.add_alternative(html, subtype='html')
            else:
                msg.set_content(body)
            client.send_message(msg)
            try:
                app.logger.debug('SMTP sent to %s via %s:%s', recipients, host, port)
            except Exception:
                pass
            # mark SENT
            try:
                from . import models
                for r in recipients:
                    try:
                        models.record_email_log(r, subject, body, status='SENT', event_id=event_id)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            try:
                app.logger.exception('SMTP send failed: %s', e)
            except Exception:
                pass
            try:
                from . import models
                for r in recipients:
                    try:
                        models.record_email_log(r, subject, body, status='FAILED', error=str(e), event_id=event_id)
                    except Exception:
                        pass
            except Exception:
                pass

    if async_send:
        t = threading.Thread(target=_send, daemon=True)
        t.start()
    else:
        _send()
