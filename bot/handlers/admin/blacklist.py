"""
Blacklist management handler.

Allows admins to manage user blacklist.
"""

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.blacklist_service import BlacklistService
from bot.keyboards.reply import admin_blacklist_keyboard, admin_keyboard, cancel_keyboard
from bot.states.admin import BlacklistStates

router = Router()


@router.message(F.text == "🚫 Управление blacklist")
async def show_blacklist(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Show blacklist management menu."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    blacklist_service = BlacklistService(session)

    active_count = await blacklist_service.count_active()
    entries = await blacklist_service.get_all_active(limit=10)

    text = (
        f"🚫 **Управление blacklist**\n\nВсего "
        f"заблокировано: {active_count}\n\n"
    )

    if entries:
        text += "**Последние записи:**\n\n"
        for entry in entries:
            from app.models.blacklist import BlacklistActionType

            action_type_text = {
                BlacklistActionType.REGISTRATION_DENIED: "Отказ в регистрации",
                BlacklistActionType.TERMINATED: "Терминация",
                BlacklistActionType.BLOCKED: "Блокировка",
            }.get(entry.action_type, entry.action_type)

            text += (
                f"ID: #{entry.id}\n"
                f"Telegram: {entry.telegram_id or 'N/A'}\n"
                f"Тип: {action_type_text}\n"
                f"Причина: {entry.reason[:30] if entry.reason else 'N/A'}...\n"
                f"─────────────────────────────\n\n"
            )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=admin_blacklist_keyboard(),
    )


@router.message(F.text == "➕ Добавить в blacklist")
async def start_add_to_blacklist(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    **data: Any,
) -> None:
    """Start adding to blacklist."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    await message.answer(
        "➕ **Добавление в blacklist**\n\n"
        "Введите Telegram ID или BSC wallet address:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(BlacklistStates.waiting_for_identifier)


@router.message(BlacklistStates.waiting_for_identifier)
async def process_blacklist_identifier(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    **data: Any,
) -> None:
    """Process identifier for blacklist."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        return

    # Check if message is a cancel button
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление в blacklist отменено.",
            reply_markup=admin_blacklist_keyboard(),
        )
        return

    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button

    if message.text and is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this

    identifier = message.text.strip()

    # Determine if telegram ID or wallet
    telegram_id = None
    wallet_address = None

    if identifier.startswith("0x") and len(identifier) == 42:
        wallet_address = identifier.lower()
    else:
        try:
            telegram_id = int(identifier)
        except ValueError:
            await message.answer(
                "❌ Неверный формат! Введите "
                "числовой Telegram ID или BSC адрес (0x...).",
                reply_markup=cancel_keyboard(),
            )
            return

    # Save to state
    await state.update_data(
        telegram_id=telegram_id,
        wallet_address=wallet_address,
    )

    await message.answer(
        "Введите причину блокировки:",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(BlacklistStates.waiting_for_reason)


@router.message(BlacklistStates.waiting_for_reason)
async def process_blacklist_reason(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    **data: Any,
) -> None:
    """Process blacklist reason."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        return

    # Check if message is a cancel button
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление в blacklist отменено.",
            reply_markup=admin_blacklist_keyboard(),
        )
        return

    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button

    if message.text and is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this

    reason = message.text.strip()

    if len(reason) < 5:
        await message.answer(
            "❌ Причина слишком короткая! Минимум 5 символов.",
            reply_markup=cancel_keyboard(),
        )
        return

    data_state = await state.get_data()
    telegram_id = data_state.get("telegram_id")
    wallet_address = data_state.get("wallet_address")

    # Get admin ID
    admin_id = None
    try:
        from app.repositories.admin_repository import AdminRepository

        admin_repo = AdminRepository(session)
        admin = await admin_repo.get_by(telegram_id=message.from_user.id)
        if admin:
            admin_id = admin.id
    except Exception:
        pass

    blacklist_service = BlacklistService(session)

    try:
        entry = await blacklist_service.add_to_blacklist(
            telegram_id=telegram_id,
            wallet_address=wallet_address,
            reason=reason,
            added_by_admin_id=admin_id,
        )

        await session.commit()

        from app.models.blacklist import BlacklistActionType

        action_type_text = {
            BlacklistActionType.REGISTRATION_DENIED: "Отказ в регистрации",
            BlacklistActionType.TERMINATED: "Терминация",
            BlacklistActionType.BLOCKED: "Блокировка",
        }.get(entry.action_type, entry.action_type)

        await message.answer(
            f"✅ **Добавлено в блеклист!**\n\n"
            f"ID: #{entry.id}\n"
            f"Telegram ID: {telegram_id or 'N/A'}\n"
            f"Тип: {action_type_text}\n"
            f"Причина: {reason}",
            parse_mode="Markdown",
            reply_markup=admin_blacklist_keyboard(),
        )

    except Exception as e:
        logger.error(f"Error adding to blacklist: {e}")
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=admin_blacklist_keyboard(),
        )

    await state.clear()


@router.message(F.text == "🗑️ Удалить из blacklist")
async def start_remove_from_blacklist(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    **data: Any,
) -> None:
    """Start removing from blacklist."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    await message.answer(
        "🗑️ **Удаление из blacklist**\n\n"
        "Введите Telegram ID или wallet address для удаления:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(BlacklistStates.waiting_for_removal_identifier)


@router.message(BlacklistStates.waiting_for_removal_identifier)
async def process_blacklist_removal(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    **data: Any,
) -> None:
    """Process blacklist removal."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        return

    # Check if message is a cancel button
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Удаление из blacklist отменено.",
            reply_markup=admin_blacklist_keyboard(),
        )
        return

    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button

    if message.text and is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this

    identifier = message.text.strip()

    telegram_id = None
    wallet_address = None

    if identifier.startswith("0x"):
        wallet_address = identifier.lower()
    else:
        try:
            telegram_id = int(identifier)
        except ValueError:
            await message.answer(
                "❌ Неверный формат!",
                reply_markup=cancel_keyboard(),
            )
            return

    blacklist_service = BlacklistService(session)

    success = await blacklist_service.remove_from_blacklist(
        telegram_id=telegram_id,
        wallet_address=wallet_address,
    )

    await session.commit()

    if success:
        await message.answer(
            "✅ **Удалено из blacklist!**\n\n"
            "Пользователь снова может использовать бота.",
            parse_mode="Markdown",
            reply_markup=admin_blacklist_keyboard(),
        )
    else:
        await message.answer(
            "❌ Запись не найдена в blacklist.",
            reply_markup=admin_blacklist_keyboard(),
        )

    await state.clear()


@router.message(F.text == "👑 Админ-панель")
async def handle_back_to_admin_panel(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Return to admin panel from blacklist menu"""
    from bot.handlers.admin.panel import handle_admin_panel_button
    
    await handle_admin_panel_button(message, session, **data)
