"""Database setup using SQLAlchemy.

This module defines the SQLAlchemy database engine and session factory for
the entire project. Configuration is read from environment variables so
that the same code can run locally via docker‑compose as well as in
production. If no explicit DATABASE_URL is provided, the individual
POSTGRES_* variables are used to construct one.

Usage:

    from common.database import Base, SessionLocal
    session = SessionLocal()
    # ... use session ...
    session.close()

You must call Base.metadata.create_all() somewhere in your application
to create tables, or use Alembic migrations for production systems.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base


# Build the database URL from individual components if necessary.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "news_portal")
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
)

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False)
)

# Base class for declarative models.
Base = declarative_base()


def init_db() -> None:
    """Initialize database tables.

    This is primarily intended for local development. In production
    deployments you should rely on Alembic migrations instead of
    creating tables directly.
    """
    # Import models here so that they are registered properly with Base.
    # pylint: disable=unused-import
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)