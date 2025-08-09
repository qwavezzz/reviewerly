"""Alembic environment configuration.

This script configures the Alembic migration context. It reads the
database URL from environment variables (if provided) and makes the
project's models available to the migration context. When running
``alembic revision --autogenerate`` the ``target_metadata`` variable
controls which tables and schemas are examined for changes.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Ensure the project root is on the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.database import Base  # noqa: E402
from common import models  # noqa: E402,F401

config = context.config

# Interpret the config file for Python logging. This line sets up loggers
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # Prefer environment variable, fall back to config
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()