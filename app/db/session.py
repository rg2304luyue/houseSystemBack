"""Synchronous SQLAlchemy 2.x session for FastAPI dependency injection."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency: yields a SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
