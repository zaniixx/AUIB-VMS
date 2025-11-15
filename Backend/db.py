from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

SessionLocal = None


def init_db(app):
    global SessionLocal
    db_url = app.config.get('DATABASE_URL')
    
    # PostgreSQL connection pool configuration
    pool_opts = {
        'pool_size': int(app.config.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(app.config.get('DB_MAX_OVERFLOW', 20)),
        'pool_timeout': int(app.config.get('DB_POOL_TIMEOUT', 60)),
        'pool_pre_ping': True  # detect stale connections
    }

    engine = create_engine(db_url, **pool_opts)
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
                                # write ISO string into start_ts
                                conn.execute(text('UPDATE events SET start_ts = :st WHERE id = :id'), {'st': dt.isoformat(), 'id': eid})
                            except Exception:
                                # ignore parse errors and leave as-is
                                pass
                    except Exception:
                        app.logger.info('No legacy date values to migrate or migration failed')
        
        # Add student_status and cgpa columns to users table if missing
        if 'users' in insp.get_table_names():
            user_cols = [c['name'] for c in insp.get_columns('users')]
            with engine.begin() as conn:
                if 'student_status' not in user_cols:
                    try:
                        conn.execute(text('ALTER TABLE users ADD COLUMN student_status VARCHAR'))
                        app.logger.info('Added student_status column to users table')
                    except Exception:
                        app.logger.info('Could not add student_status column to users (may not be supported by this DB)')
                if 'cgpa' not in user_cols:
                    try:
                        conn.execute(text('ALTER TABLE users ADD COLUMN cgpa FLOAT'))
                        app.logger.info('Added cgpa column to users table')
                    except Exception:
                        app.logger.info('Could not add cgpa column to users (may not be supported by this DB)')
        
        # Add student_status and cgpa columns to timelogs table if missing
        if 'timelogs' in insp.get_table_names():
            timelog_cols = [c['name'] for c in insp.get_columns('timelogs')]
            with engine.begin() as conn:
                if 'student_status' not in timelog_cols:
                    try:
                        conn.execute(text('ALTER TABLE timelogs ADD COLUMN student_status VARCHAR'))
                        app.logger.info('Added student_status column to timelogs table')
                    except Exception:
                        app.logger.info('Could not add student_status column to timelogs (may not be supported by this DB)')
                if 'cgpa' not in timelog_cols:
                    try:
                        conn.execute(text('ALTER TABLE timelogs ADD COLUMN cgpa FLOAT'))
                        app.logger.info('Added cgpa column to timelogs table')
                    except Exception:
                        app.logger.info('Could not add cgpa column to timelogs (may not be supported by this DB)')
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
