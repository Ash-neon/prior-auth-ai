"""
Alembic Environment Configuration
==================================

Configures Alembic for database migrations with support for:
- Environment variable configuration
- Auto-detection of model changes
- Multi-tenant schema awareness
- HIPAA-compliant logging

Author: Prior Auth AI Team
Version: 1.0.0
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import models and configuration
from backend.core.config import settings
from backend.db.base import Base
from backend.models import *  # Import all models for auto-detection

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from environment variables.
    
    Returns:
        Database connection URL
    """
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override sqlalchemy.url with environment variable
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    # Create engine with connection pooling disabled for migrations
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
            compare_server_default=True,
            # Include schemas if using multi-schema setup
            # include_schemas=True,
            # version_table_schema=target_metadata.schema,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()