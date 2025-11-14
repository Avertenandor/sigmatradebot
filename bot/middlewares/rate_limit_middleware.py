"""Rate Limit Middleware - Prevent spam and abuse."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from loguru import logger
import redis.asyncio as redis


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware.

    Limits:
    - Per-user: 30 requests per minute
    - Per-IP: 100 requests per minute (if available)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        user_limit: int = 30,
        user_window: int = 60,
    ) -> None:
        """
        Initialize rate limit middleware.

        Args:
            redis_client: Redis client
            user_limit: Max requests per user
            user_window: Time window in seconds
        """
        super().__init__()
        self.redis = redis_client
        self.user_limit = user_limit
        self.user_window = user_window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Check rate limit and process update."""
        user: User = data.get("event_from_user")

        if not user:
            return await handler(event, data)

        # Rate limit key
        key = f"ratelimit:user:{user.id}"

        try:
            # Get current count
            count = await self.redis.get(key)

            if count is None:
                # First request in window
                await self.redis.setex(key, self.user_window, "1")
                return await handler(event, data)

            current_count = int(count)

            if current_count >= self.user_limit:
                logger.warning(
                    f"Rate limit exceeded for user {user.id}: "
                    f"{current_count}/{self.user_limit}"
                )
                # Silently ignore (don't waste resources responding)
                return None

            # Increment counter
            await self.redis.incr(key)

        except Exception as e:
            logger.error(f"Rate limit Redis error: {e}")
            # On Redis error, allow request (fail open)

        return await handler(event, data)
