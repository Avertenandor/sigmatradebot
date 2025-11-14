"""
Blacklist model.

Tracks banned users with reason and admin who banned them.
"""

from typing import Optional

from sqlalchemy import BigInteger, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Blacklist(Base):
    """
    Blacklist entity.

    Represents a banned user:
    - Telegram ID of banned user
    - Ban reason
    - Admin who banned them

    Attributes:
        id: Primary key
        telegram_id: Banned user's Telegram ID
        reason: Ban reason (optional)
        created_by_admin_id: Admin ID who created ban
        created_at: Ban timestamp
    """

    __tablename__ = "blacklist"

    # Banned user
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )

    # Ban details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Admin who banned (stored as int, no FK for simplicity)
    created_by_admin_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"Blacklist(id={self.id}, telegram_id={self.telegram_id})"
