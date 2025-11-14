"""Alembic migration environment."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import models to ensure they're registered with MetaData
from app.models.base import Base  # noqa: F401

# Import all models (must be imported for alembic to detect them)
from app.models.admin import Admin, AdminSession  # noqa: F401
from app.models.blacklist import Blacklist  # noqa: F401
from app.models.deposit import Deposit  # noqa: F401
from app.models.deposit_reward import DepositReward  # noqa: F401
from app.models.failed_notification import FailedNotification  # noqa: F401
from app.models.financial_password_recovery import (  # noqa: F401
    FinancialPasswordRecovery,
)
from app.models.payment_retry import PaymentRetry  # noqa: F401
from app.models.referral import Referral  # noqa: F401
from app.models.referral_earning import ReferralEarning  # noqa: F401
from app.models.reward_session import RewardSession  # noqa: F401
from app.models.support_message import SupportMessage  # noqa: F401
from app.models.support_ticket import SupportTicket  # noqa: F401
from app.models.system_setting import SystemSetting  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_action import UserAction  # noqa: F401
from app.models.wallet_change_request import WalletChangeRequest  # noqa: F401

# Get database URL from settings
from app.config import get_settings

settings = get_settings()

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Target metadata from models
target_metadata = Base.metadata


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
    url = config.get_main_option("sqlalchemy.url")
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


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode (async)."""
    configuration = config.get_section(config.config_ini_section, {})

    # Create async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
