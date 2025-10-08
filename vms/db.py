from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

SessionLocal = None


def init_db(app):
    global SessionLocal
    db_url = app.config.get('DATABASE_URL')
    engine = create_engine(db_url, connect_args={'check_same_thread': False} if db_url.startswith('sqlite') else {})
    SessionLocal = scoped_session(sessionmaker(bind=engine))

    # import models and create tables
    from . import models as _models
    _models.Base.metadata.create_all(bind=engine)

    # lightweight automatic migration: add start_ts/end_ts columns to events if missing,
    # and migrate legacy `date` string into start_ts where possible.
    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine)
        if 'events' in insp.get_table_names():
            cols = [c['name'] for c in insp.get_columns('events')]
            with engine.begin() as conn:
                # add missing columns
                if 'start_ts' not in cols:
                    try:
                        conn.execute(text('ALTER TABLE events ADD COLUMN start_ts DATETIME'))
                    except Exception:
                        app.logger.info('Could not add start_ts column to events (may not be supported by this DB)')
                if 'end_ts' not in cols:
                    try:
                        conn.execute(text('ALTER TABLE events ADD COLUMN end_ts DATETIME'))
                    except Exception:
                        app.logger.info('Could not add end_ts column to events (may not be supported by this DB)')

                # migrate legacy `date` values into start_ts if `date` column exists
                if 'date' in cols:
                    try:
                        rows = conn.execute(text("SELECT id, date FROM events WHERE date IS NOT NULL")).fetchall()
                        import datetime as _dt
                        for r in rows:
                            eid = r[0]
                            raw = r[1]
                            if not raw:
                                continue
                            try:
                                dt = _dt.datetime.fromisoformat(raw)
                                # write ISO string into start_ts (SQLite stores as text)
                                conn.execute(text('UPDATE events SET start_ts = :st WHERE id = :id'), {'st': dt.isoformat(), 'id': eid})
                            except Exception:
                                # ignore parse errors and leave as-is
                                pass
                    except Exception:
                        app.logger.info('No legacy date values to migrate or migration failed')
    except Exception:
        try:
            app.logger.exception('Automatic DB migration check failed')
        except Exception:
            pass


def get_db():
    global SessionLocal
    if SessionLocal is None:
        raise RuntimeError('DB not initialized')
    return SessionLocal()


def close_db():
    global SessionLocal
    if SessionLocal:
        SessionLocal.remove()
