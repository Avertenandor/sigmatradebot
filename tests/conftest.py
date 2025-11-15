"""
Pytest configuration and fixtures for bot testing.

This module provides fixtures for testing Telegram bot without real Telegram API.
Uses aiogram's MockBot and MockDispatcher for e2e testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat, Message, CallbackQuery, Update
from aiogram.methods import SendMessage, AnswerCallbackQuery

from app.config.database import async_session_maker
from app.config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_bot() -> Bot:
    """
    Create a mock Bot instance for testing.
    
    Uses MockBot which doesn't require real Telegram API.
    """
    from aiogram.client.bot import Bot
    from aiogram.client.session.memory import MemorySession
    
    # Use MemorySession to avoid real API calls
    session = MemorySession()
    bot = Bot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", session=session)
    
    yield bot
    
    await bot.session.close()


@pytest.fixture
async def mock_dispatcher(mock_bot: Bot) -> Dispatcher:
    """
    Create a mock Dispatcher for testing.
    
    Uses MemoryStorage for FSM states.
    """
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middlewares (simplified for testing)
    from bot.middlewares.database import DatabaseMiddleware
    from bot.middlewares.auth import AuthMiddleware
    
    dp.update.middleware(DatabaseMiddleware(session_pool=async_session_maker))
    dp.update.middleware(AuthMiddleware())
    
    # Register all handlers
    from bot.handlers import (
        start, menu, deposit, withdrawal, referral,
        profile, transaction, support, finpass_recovery, instructions
    )
    from bot.handlers.admin import (
        panel, users, withdrawals, broadcast, blacklist,
        deposit_settings, finpass_recovery as admin_finpass,
        management, wallets, wallet_key_setup
    )
    
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(deposit.router)
    dp.include_router(withdrawal.router)
    dp.include_router(referral.router)
    dp.include_router(profile.router)
    dp.include_router(transaction.router)
    dp.include_router(support.router)
    dp.include_router(finpass_recovery.router)
    dp.include_router(instructions.router)
    
    dp.include_router(wallet_key_setup.router)
    dp.include_router(panel.router)
    dp.include_router(users.router)
    dp.include_router(withdrawals.router)
    dp.include_router(broadcast.router)
    dp.include_router(blacklist.router)
    dp.include_router(deposit_settings.router)
    dp.include_router(admin_finpass.router)
    dp.include_router(management.router)
    dp.include_router(wallets.router)
    
    yield dp


@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram user."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="en"
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram chat."""
    return Chat(
        id=123456789,
        type="private",
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def mock_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock Telegram message."""
    return Message(
        message_id=1,
        date=1234567890,
        chat=mock_chat,
        from_user=mock_user,
        text="/start"
    )


@pytest.fixture
def mock_callback_query(mock_user: User, mock_chat: Chat) -> CallbackQuery:
    """Create a mock Telegram callback query."""
    return CallbackQuery(
        id="test_callback_id",
        from_user=mock_user,
        chat_instance="test_chat_instance",
        data="menu:main"
    )


@pytest.fixture
async def db_session():
    """Create a database session for testing."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(db_session):
    """Create a test user in database."""
    from app.models.user import User
    from app.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db_session)
    
    # Check if user exists
    user = await user_repo.get_by_telegram_id(123456789)
    if not user:
        user = User(
            telegram_id=123456789,
            username="testuser",
            balance=0.0,
            wallet_address="0x0000000000000000000000000000000000000000",
            financial_password_hash="test_hash"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    
    yield user
    
    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.fixture
async def test_admin(db_session):
    """Create a test admin in database."""
    from app.models.admin import Admin
    from app.repositories.admin_repository import AdminRepository
    
    admin_repo = AdminRepository(db_session)
    
    admin = await admin_repo.get_by_telegram_id(999999999)
    if not admin:
        admin = Admin(
            telegram_id=999999999,
            username="testadmin",
            role="admin"
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)
    
    yield admin
    
    # Cleanup
    await db_session.delete(admin)
    await db_session.commit()

