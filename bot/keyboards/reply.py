"""
Reply keyboards.

Reply keyboard builders for main navigation.
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Main menu reply keyboard.

    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="💰 Депозит"),
        KeyboardButton(text="💸 Вывод"),
    )
    builder.row(
        KeyboardButton(text="👥 Рефералы"),
        KeyboardButton(text="📊 Баланс"),
    )
    builder.row(
        KeyboardButton(text="💬 Поддержка"),
        KeyboardButton(text="⚙️ Настройки"),
    )

    return builder.as_markup(resize_keyboard=True)
