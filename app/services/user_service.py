"""
User service.

Business logic for user management.
"""

from typing import Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.blacklist_repository import (
    BlacklistRepository,
)


class UserService:
    """
    User service.

    Handles user registration, profile management, and referrals.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize user service.

        Args:
            session: Database session
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.blacklist_repo = BlacklistRepository(session)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return await self.user_repo.get_by_id(user_id)

    async def get_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User or None
        """
        return await self.user_repo.get_by_telegram_id(
            telegram_id
        )

    async def register_user(
        self,
        telegram_id: int,
        wallet_address: str,
        financial_password: str,
        username: Optional[str] = None,
        referrer_telegram_id: Optional[int] = None,
    ) -> User:
        """
        Register new user with referral support.

        Args:
            telegram_id: Telegram user ID
            wallet_address: User's wallet address
            financial_password: Bcrypt-hashed password
            username: Telegram username (optional)
            referrer_telegram_id: Referrer's Telegram ID

        Returns:
            Created user

        Raises:
            ValueError: If user already exists or blacklisted
        """
        # Check if blacklisted
        is_blacklisted = await self.blacklist_repo.is_blacklisted(
            telegram_id
        )
        if is_blacklisted:
            raise ValueError("User is blacklisted")

        # Check if already exists
        existing = await self.user_repo.get_by_telegram_id(
            telegram_id
        )
        if existing:
            raise ValueError("User already registered")

        # Find referrer if provided
        referrer_id = None
        if referrer_telegram_id:
            referrer = await self.user_repo.get_by_telegram_id(
                referrer_telegram_id
            )
            if referrer:
                referrer_id = referrer.id

        # Create user
        user = await self.user_repo.create(
            telegram_id=telegram_id,
            username=username,
            wallet_address=wallet_address,
            financial_password=financial_password,
            referrer_id=referrer_id,
        )

        await self.session.commit()

        logger.info(
            "User registered",
            extra={
                "user_id": user.id,
                "telegram_id": telegram_id,
                "has_referrer": referrer_id is not None,
            },
        )

        return user

    async def update_profile(
        self, user_id: int, **data
    ) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User ID
            **data: Fields to update

        Returns:
            Updated user or None
        """
        user = await self.user_repo.update(user_id, **data)

        if user:
            await self.session.commit()
            logger.info(
                "User profile updated",
                extra={"user_id": user_id},
            )

        return user

    async def block_earnings(
        self, user_id: int, block: bool = True
    ) -> Optional[User]:
        """
        Block/unblock user earnings.

        Used during financial password recovery.

        Args:
            user_id: User ID
            block: True to block, False to unblock

        Returns:
            Updated user or None
        """
        return await self.update_profile(
            user_id, earnings_blocked=block
        )

    async def ban_user(
        self, user_id: int, ban: bool = True
    ) -> Optional[User]:
        """
        Ban/unban user.

        Args:
            user_id: User ID
            ban: True to ban, False to unban

        Returns:
            Updated user or None
        """
        return await self.update_profile(user_id, is_banned=ban)

    async def get_all_telegram_ids(self) -> list[int]:
        """
        Get all user Telegram IDs.

        Returns:
            List of Telegram IDs
        """
        return await self.user_repo.get_all_telegram_ids()

    async def verify_financial_password(
        self, user_id: int, password: str
    ) -> bool:
        """
        Verify financial password.

        Args:
            user_id: User ID
            password: Plain password to verify

        Returns:
            True if password matches
        """
        import bcrypt

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        return bcrypt.checkpw(
            password.encode(),
            user.financial_password.encode(),
        )

    async def unban_user(self, user_id: int) -> dict:
        """
        Unban user.

        Args:
            user_id: User ID

        Returns:
            Result dict with success status
        """
        user = await self.set_ban(user_id, False)
        if user:
            return {"success": True}
        return {"success": False, "error": "User not found"}

    async def get_total_users(self) -> int:
        """
        Get total number of users.

        Returns:
            Total user count
        """
        return await self.user_repo.count()

    async def get_verified_users(self) -> int:
        """
        Get number of verified users.

        Returns:
            Verified user count
        """
        users = await self.user_repo.find_by(is_verified=True)
        return len(users)

    async def get_user_stats(self, user_id: int) -> dict:
        """
        Get user statistics.

        Args:
            user_id: User ID

        Returns:
            User stats dict
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {}

        # Get deposits total (stub - should query deposits)
        total_deposits = Decimal("0.00")

        # Get referral count (stub - should query referrals)
        referral_count = 0

        # Get activated levels (stub - should query deposits)
        activated_levels = []

        return {
            "total_deposits": total_deposits,
            "referral_count": referral_count,
            "activated_levels": activated_levels,
        }

    async def get_user_balance(self, user_id: int) -> dict:
        """
        Get user balance.

        Args:
            user_id: User ID

        Returns:
            Balance dict
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {
                "available_balance": Decimal("0.00"),
                "total_earned": Decimal("0.00"),
                "pending_earnings": Decimal("0.00"),
                "pending_withdrawals": Decimal("0.00"),
                "total_paid": Decimal("0.00"),
            }

        # Return user balance fields
        return {
            "available_balance": getattr(user, "balance", Decimal("0.00")),
            "total_earned": getattr(user, "total_earned", Decimal("0.00")),
            "pending_earnings": getattr(user, "pending_earnings", Decimal("0.00")),
            "pending_withdrawals": Decimal("0.00"),  # Should query withdrawals
            "total_paid": Decimal("0.00"),  # Should query transactions
        }

    async def generate_referral_link(self, user_id: int, bot_username: str) -> str:
        """
        Generate referral link for user.

        Args:
            user_id: User ID
            bot_username: Bot username

        Returns:
            Referral link
        """
        return f"https://t.me/{bot_username}?start=ref_{user_id}"

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by ID (alias for get_by_id).

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return await self.user_repo.get_by_id(user_id)

    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username.

        Args:
            username: Username (without @)

        Returns:
            User or None
        """
        users = await self.user_repo.find_by(username=username)
        return users[0] if users else None

    async def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Find user by Telegram ID.

        Args:
            telegram_id: Telegram ID

        Returns:
            User or None
        """
        users = await self.user_repo.find_by(telegram_id=telegram_id)
        return users[0] if users else None
