"""Alembic environment script for laboratory_service.

Reads DATABASE_URL from the LABORATORY_SVC_DATABASE_URL environment variable
and drives both offline and online migration modes.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.domain.models import Base

# Alembic Config object providing access to values in alembic.ini.
config = context.config

# Interpret the ini-file's logging configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object used for autogenerate support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Execute migrations in 'offline' mode (no live DB connection required)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Execute migrations in 'online' mode using an async engine."""
    connectable: AsyncEngine = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


import asyncio

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
