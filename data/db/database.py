"""Database connection and session handling module for CivicConnect.

Provides SQLAlchemy engine, session factory, and DB table creation utilities.
Uses DATABASE_URL from environment with fallback support.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from data.db.models import Base

# Fetch DATABASE_URL from environment or fallback to sqlite for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./civicconnect.db")

# Fix potential postgres:// vs postgresql:// prefix issues in SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine connect args if SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully using URL: {DATABASE_URL}")
