from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from flask import current_app


class Base(DeclarativeBase):
    pass


def get_engine():
    return create_engine(
        current_app.config["DATABASE_URL"],
        pool_pre_ping=True,
    )


def get_session():
    engine  = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Cria a extensão pgvector e todas as tabelas."""
    from app.database import models  # noqa: F401
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)
