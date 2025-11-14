"""
Keyboards.

Telegram keyboards (inline and reply).
"""

from bot.keyboards.inline import (
    admin_keyboard,
    deposit_keyboard,
    main_menu_keyboard,
    referral_keyboard,
    support_keyboard,
    withdrawal_keyboard,
)
from bot.keyboards.reply import main_menu_reply_keyboard

__all__ = [
    # Inline keyboards
    "admin_keyboard",
    "deposit_keyboard",
    "main_menu_keyboard",
    "referral_keyboard",
    "support_keyboard",
    "withdrawal_keyboard",
    # Reply keyboards
    "main_menu_reply_keyboard",
]
