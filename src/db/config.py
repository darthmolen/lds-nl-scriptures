"""Database configuration module.

Provides SQLAlchemy engine and session management for the Scripture Search project.
Uses synchronous psycopg2 driver for data ingestion tasks.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL_SYNC environment variable is not set. "
        "Please configure it in your .env file."
    )

# Create SQLAlchemy engine
# Using pool_pre_ping to handle dropped connections gracefully
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Usage:
        with get_session() as session:
            session.add(some_object)
            session.commit()

    Yields:
        Session: SQLAlchemy session object

    Note:
        The session is automatically closed when exiting the context.
        Commits must be done explicitly within the context.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
