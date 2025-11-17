"""
Deposit settings handler.

Allows admins to configure max open deposit level.
"""

import re
from typing import Any

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.settings_service import SettingsService
from bot.keyboards.reply import admin_deposit_settings_keyboard, admin_keyboard

router = Router()


@router.message(F.text == "⚙️ Настроить уровни депозитов")
async def show_deposit_settings(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Show deposit settings."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    settings_service = SettingsService(session)

    max_level = await settings_service.get_int(
        "max_open_deposit_level", default=5
    )

    text = (
        "⚙️ **Настройки депозитов**\n\n"
        f"Максимальный открытый уровень: **{max_level}**\n\n"
        "Пользователи могут создавать депозиты только до указанного уровня.\n\n"
        "Уровни:\n"
        "1️⃣ Уровень 1\n"
        "2️⃣ Уровень 2\n"
        "3️⃣ Уровень 3\n"
        "4️⃣ Уровень 4\n"
        "5️⃣ Уровень 5\n\n"
        "Для установки максимального уровня введите: **уровень <номер>**\n"
        "Пример: `уровень 3`"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=admin_deposit_settings_keyboard(),
    )


@router.message(F.text.regexp(r"^уровень\s+(\d+)$", flags=0))
async def set_max_deposit_level(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Set max deposit level."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    # Extract level from message text
    match = re.match(r"^уровень\s+(\d+)$", message.text.strip(), re.IGNORECASE)
    if not match:
        await message.answer(
            "❌ Неверный формат. Используйте: `уровень <номер>` (1-5)",
            reply_markup=admin_deposit_settings_keyboard(),
        )
        return

    level = int(match.group(1))
    
    if level < 1 or level > 5:
        await message.answer(
            "❌ Уровень должен быть от 1 до 5",
            reply_markup=admin_deposit_settings_keyboard(),
        )
        return

    # Get admin
    from app.repositories.admin_repository import AdminRepository
    
    admin_repo = AdminRepository(session)
    admin = await admin_repo.get_by(telegram_id=message.from_user.id)
    
    if not admin:
        await message.answer(
            "❌ Администратор не найден",
            reply_markup=admin_deposit_settings_keyboard(),
        )
        return

    settings_service = SettingsService(session)

    await settings_service.set(
        key="max_open_deposit_level",
        value=level,
        description=f"Maximum open deposit level (set by admin {admin.telegram_id})",
    )

    await session.commit()

    await message.answer(
        f"✅ Максимальный уровень установлен: {level}",
        reply_markup=admin_deposit_settings_keyboard(),
    )

    # Refresh display
    await show_deposit_settings(message, session, **data)


@router.message(F.text == "👑 Админ-панель")
async def handle_back_to_admin_panel(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Return to admin panel from deposit settings menu"""
    from bot.handlers.admin.panel import handle_admin_panel_button
    
    await handle_admin_panel_button(message, session, **data)
