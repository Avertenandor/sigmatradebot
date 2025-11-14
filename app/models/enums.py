"""
Database enums.

Centralized enums used across database models.
"""

from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status values."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class TransactionType(str, Enum):
    """Transaction type values."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFERRAL_REWARD = "referral_reward"
    DEPOSIT_REWARD = "deposit_reward"
    SYSTEM_PAYOUT = "system_payout"


class WalletChangeType(str, Enum):
    """Wallet change request type values."""

    SYSTEM_DEPOSIT = "system_deposit"
    PAYOUT_WITHDRAWAL = "payout_withdrawal"


class WalletChangeStatus(str, Enum):
    """Wallet change request status values."""

    PENDING = "pending"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


class SupportTicketStatus(str, Enum):
    """Support ticket status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicketPriority(str, Enum):
    """Support ticket priority values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SupportCategory(str, Enum):
    """Support ticket category values."""

    PAYMENTS = "payments"
    WITHDRAWALS = "withdrawals"
    FINPASS = "finpass"
    REFERRALS = "referrals"
    TECH = "tech"
    OTHER = "other"


class SupportSender(str, Enum):
    """Support message sender values."""

    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
