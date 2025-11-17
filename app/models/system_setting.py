"""
SystemSetting model.

Stores runtime configuration settings.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemSetting(Base):
    """
    SystemSetting entity.

    Stores runtime configuration:
    - Key-value pairs
    - Cacheable settings with TTL
    - Examples: DEPOSITS_MAX_OPEN_LEVEL (1-5)

    Attributes:
        key: Setting key (primary key)
        value: Setting value (text)
        updated_at: Last update timestamp
    """

    __tablename__ = "system_settings"

    # Primary Key (using key instead of id)
    key: Mapped[str] = mapped_column(
        String(100), primary_key=True, nullable=False
    )

    # Value
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"SystemSetting(key={self.key!r}, value={self.value!r})"
