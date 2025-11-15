"""
Deposit settings handler.

Allows admins to configure max open deposit level.
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.settings_service import SettingsService
from bot.states.admin import DepositSettingsStates

router = Router()


@router.callback_query(lambda c: c.data == "admin:deposit_settings")
async def show_deposit_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Show deposit settings."""
    settings_service = SettingsService(session)

    max_level = await settings_service.get_int("max_open_deposit_level", default=5)

    text = (
        "⚙️ **Настройки депозитов**\n\n"
        f"Максимальный открытый уровень: **{max_level}**\n\n"
        "Пользователи могут создавать депозиты только до указанного уровня.\n\n"
        "Уровни:\n"
        "1️⃣ Уровень 1\n"
        "2️⃣ Уровень 2\n"
        "3️⃣ Уровень 3\n"
        "4️⃣ Уровень 4\n"
        "5️⃣ Уровень 5\n"
    )

    builder = InlineKeyboardBuilder()

    for level in range(1, 6):
        emoji = "✅" if level <= max_level else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} Уровень {level}",
                callback_data=f"admin:set_max_level:{level}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin:panel",
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:set_max_level:"))
async def set_max_deposit_level(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Set max deposit level."""
    level = int(callback.data.split(":")[-1])

    settings_service = SettingsService(session)

    await settings_service.set(
        key="max_open_deposit_level",
        value=level,
        description=f"Maximum open deposit level (set by admin {admin.telegram_id})",
    )

    await session.commit()

    await callback.answer(
        f"✅ Максимальный уровень установлен: {level}",
        show_alert=True,
    )

    # Refresh display
    await show_deposit_settings(callback, session, admin)
