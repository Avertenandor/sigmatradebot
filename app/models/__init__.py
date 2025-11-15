"""
Database models.

Exports all SQLAlchemy models for easy imports.
"""

from app.models.base import Base
from app.models.enums import (
    TransactionStatus,
    TransactionType,
    WalletChangeStatus,
    WalletChangeType,
    SupportTicketStatus,
    SupportTicketPriority,
    SupportCategory,
    SupportSender,
)

# Core Models
from app.models.user import User
from app.models.deposit import Deposit
from app.models.transaction import Transaction
from app.models.referral import Referral

# Admin Models
from app.models.admin import Admin
from app.models.admin_session import AdminSession

# Security Models
from app.models.blacklist import Blacklist
from app.models.financial_password_recovery import (
    FinancialPasswordRecovery,
)
from app.models.appeal import Appeal, AppealStatus

# Reward Models
from app.models.reward_session import RewardSession
from app.models.deposit_reward import DepositReward
from app.models.referral_earning import ReferralEarning

# КРИТИЧНЫЕ модели из PART5
from app.models.payment_retry import PaymentRetry, PaymentType
from app.models.failed_notification import FailedNotification

# Support Models
from app.models.support_ticket import SupportTicket
from app.models.support_message import SupportMessage

# System Models
from app.models.system_setting import SystemSetting
from app.models.user_action import UserAction
from app.models.wallet_change_request import WalletChangeRequest

__all__ = [
    # Base
    "Base",
    # Enums
    "TransactionStatus",
    "TransactionType",
    "WalletChangeStatus",
    "WalletChangeType",
    "SupportTicketStatus",
    "SupportTicketPriority",
    "SupportCategory",
    "SupportSender",
    "PaymentType",
    # Core Models
    "User",
    "Deposit",
    "Transaction",
    "Referral",
    # Admin Models
    "Admin",
    "AdminSession",
    # Security Models
    "Blacklist",
    "FinancialPasswordRecovery",
    "Appeal",
    "AppealStatus",
    # Reward Models
    "RewardSession",
    "DepositReward",
    "ReferralEarning",
    # PART5 Critical Models
    "PaymentRetry",
    "FailedNotification",
    # Support Models
    "SupportTicket",
    "SupportMessage",
    # System Models
    "SystemSetting",
    "UserAction",
    "WalletChangeRequest",
]
