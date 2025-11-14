"""
Deposit model.

Represents user deposits into the platform.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Deposit(Base):
    """Deposit model - user deposits."""

    __tablename__ = "deposits"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Deposit details
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )  # 1-5
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 8), nullable=False
    )

    # Blockchain data
    tx_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    block_number: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, confirmed, failed

    # ROI tracking
    roi_cap_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 8), nullable=False, default=Decimal("0")
    )
    roi_paid_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 8), nullable=False, default=Decimal("0")
    )
    is_roi_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="deposits",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Deposit(id={self.id}, user_id={self.user_id}, "
            f"level={self.level}, amount={self.amount}, status={self.status})>"
        )
