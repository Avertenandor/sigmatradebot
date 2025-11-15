"""
Bot main entry point.

Initializes and runs the Telegram bot with aiogram 3.x.
"""

import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import async_session_maker
from bot.middlewares.ban_middleware import BanMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.logger_middleware import LoggerMiddleware
from bot.middlewares.rate_limit_middleware import RateLimitMiddleware
from bot.middlewares.request_id import RequestIDMiddleware


async def main() -> None:
    """Initialize and run the bot."""
    # Configure logger
    logger.add(
        "logs/bot.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
    )

    logger.info("Starting SigmaTrade Bot...")

    # Get settings
    settings = get_settings()

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN,
        ),
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register middlewares (PART5: RequestID must be first!)
    dp.update.middleware(RequestIDMiddleware())
    dp.update.middleware(LoggerMiddleware())
    dp.update.middleware(
        DatabaseMiddleware(session_pool=async_session_maker)
    )
    dp.update.middleware(BanMiddleware())

    # Rate limiting (requires Redis)
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(settings.redis_url)
        dp.update.middleware(
            RateLimitMiddleware(
                redis_client=redis_client,
                user_limit=settings.rate_limit_max_requests_per_user,
                user_window=settings.rate_limit_window_ms // 1000,
            )
        )
        logger.info("Rate limiting enabled")
    except Exception as e:
        logger.warning(f"Rate limiting disabled: {e}")

    # Register handlers
    from bot.handlers import (
        deposit,
        finpass_recovery,
        instructions,
        menu,
        profile,
        referral,
        start,
        support,
        transaction,
        withdrawal,
    )
    from bot.handlers.admin import (
        blacklist,
        broadcast,
        deposit_settings,
        finpass_recovery as admin_finpass,
        management,
        panel,
        users,
        wallets,
        withdrawals,
    )

    # Core handlers
    dp.include_router(start.router)
    dp.include_router(menu.router)

    # User handlers
    dp.include_router(deposit.router)
    dp.include_router(withdrawal.router)
    dp.include_router(referral.router)
    dp.include_router(profile.router)
    dp.include_router(transaction.router)
    dp.include_router(support.router)
    dp.include_router(instructions.router)
    dp.include_router(finpass_recovery.router)

    # Admin handlers
    dp.include_router(panel.router)
    dp.include_router(users.router)
    dp.include_router(withdrawals.router)
    dp.include_router(broadcast.router)
    dp.include_router(management.router)
    dp.include_router(deposit_settings.router)
    dp.include_router(wallets.router)
    dp.include_router(admin_finpass.router)
    dp.include_router(blacklist.router)

    # Start polling
    logger.info("Bot started successfully")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        sys.exit(1)
