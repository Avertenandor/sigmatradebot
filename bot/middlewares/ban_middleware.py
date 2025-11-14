"""Ban Middleware - Block banned users."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from loguru import logger


class BanMiddleware(BaseMiddleware):
    """
    Middleware to block banned users.

    Prevents banned users from interacting with the bot.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Process update and check if user is banned.

        Args:
            handler: Next handler
            event: Telegram event
            data: Handler data

        Returns:
            Handler result or None if banned
        """
        # Get user from event
        user: User = data.get("event_from_user")

        if not user:
            return await handler(event, data)

        # Get database session
        session = data.get("session")

        if not session:
            logger.warning("No database session in middleware data")
            return await handler(event, data)

        # Check if user is banned (import here to avoid circular dependency)
        from app.repositories.user_repository import UserRepository

        user_repo = UserRepository(session)
        db_user = await user_repo.find_by_telegram_id(user.id)

        if db_user and db_user.is_banned:
            logger.info(f"Banned user attempted to use bot: {user.id}")
            # Silently ignore (don't respond to banned users)
            return None

        # User not banned, continue
        return await handler(event, data)
