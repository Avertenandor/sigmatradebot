"""
Database middleware.

Provides database session factory to handlers for proper transaction management.
Session lifecycle is controlled by handlers, not middleware.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    """
    Database middleware - provides session factory to handlers.
    
    IMPORTANT: This middleware provides session_factory, NOT a live session.
    Each handler must manage its own session lifecycle to avoid long-running
    transactions during FSM states or async operations.
    """

    def __init__(self, session_pool: async_sessionmaker) -> None:
        """
        Initialize database middleware.

        Args:
            session_pool: SQLAlchemy async session maker
        """
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Provide database session factory to handler.
        
        Handler is responsible for:
        1. Creating session via: async with session_factory() as session
        2. Managing transaction via: async with session.begin()
        3. Ensuring session is closed after use
        
        This approach prevents long-running transactions during FSM waits.

        Args:
            handler: Next handler
            event: Telegram event
            data: Handler data

        Returns:
            Handler result
        """
        # Provide session factory, not live session
        data["session_factory"] = self.session_pool
        
        # For backward compatibility during migration, also provide session
        # TODO: Remove after full migration to session_factory pattern
        async with self.session_pool() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
