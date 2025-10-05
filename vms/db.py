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


def get_db():
    global SessionLocal
    if SessionLocal is None:
        raise RuntimeError('DB not initialized')
    return SessionLocal()


def close_db():
    global SessionLocal
    if SessionLocal:
        SessionLocal.remove()
        