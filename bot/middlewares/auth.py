"""
Auth middleware.

Checks if user is registered and loads user data.
"""

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthMiddleware(BaseMiddleware):
    """
    Auth middleware.

    Loads user from database and adds to handler data.
    """

    def __init__(self, require_registration: bool = False) -> None:
        """
        Initialize auth middleware.

        Args:
            require_registration: If True, blocks unregistered users
        """
        super().__init__()
        self.require_registration = require_registration

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Load user and check registration.

        Args:
            handler: Next handler
            event: Telegram event
            data: Handler data

        Returns:
            Handler result
        """
        # Get session from data (provided by DatabaseMiddleware)
        session: AsyncSession = data.get("session")
        if not session:
            logger.error("No session in data - DatabaseMiddleware missing?")
            return

        # Get telegram user
        telegram_user = None
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user

        if not telegram_user:
            # No user in event, skip
            return await handler(event, data)

        # Load user from database
        user_repo = UserRepository(session)
        users = await user_repo.find_by(
            telegram_id=telegram_user.id
        )
        user: Optional[User] = users[0] if users else None

        # Add user to data
        data["user"] = user

        # Check if registration required
        if self.require_registration and not user:
            # User not registered - block access
            if isinstance(event, Message):
                await event.answer(
                    "Вы не зарегистрированы! "
                    "Используйте /start для регистрации."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "Вы не зарегистрированы! "
                    "Используйте /start для регистрации.",
                    show_alert=True,
                )
            return

        # Call next handler
        return await handler(event, data)
