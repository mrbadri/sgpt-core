"""Alembic environment configuration."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Add src/ to path so app.* imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.settings import settings  # noqa: E402

# Import all SQLModel table models so their metadata is registered
from app.models import User, UserIdentity, Message, Payment, UserSubscription  # noqa: F401, E402

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel.metadata tracks all SQLModel table=True models
target_metadata = SQLModel.metadata


def _render_item(type_: str, obj, autogen_context) -> str | bool:
    """Emit ``sa.String`` for SQLModel ``AutoString`` so revisions need no sqlmodel import."""
    if type_ != "type":
        return False
    try:
        from sqlmodel.sql.sqltypes import AutoString
    except ImportError:
        return False
    if isinstance(obj, AutoString):
        if obj.length is not None:
            return f"sa.String(length={int(obj.length)})"
        return "sa.String(length=255)"
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=_render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=_render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
