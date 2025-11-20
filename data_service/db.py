"""Database session helpers for the data service."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope():
    """Provide a transactional scope for raw SQL statements."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db():
    """FastAPI dependency that yields a session."""
    with session_scope() as session:
        yield session
