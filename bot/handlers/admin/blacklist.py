"""
Blacklist management handler.

Allows admins to manage user blacklist.
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.blacklist_service import BlacklistService
from bot.states.admin import BlacklistStates

router = Router()


@router.callback_query(lambda c: c.data == "admin:blacklist")
async def show_blacklist(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Show blacklist management menu."""
    blacklist_service = BlacklistService(session)

    active_count = await blacklist_service.count_active()
    entries = await blacklist_service.get_all_active(limit=10)

    text = f"🚫 **Управление блеклистом**\n\nВсего заблокировано: {active_count}\n\n"

    if entries:
        text += "**Последние записи:**\n\n"
        for entry in entries:
            text += (
                f"ID: #{entry.id}\n"
                f"Telegram: {entry.telegram_id or 'N/A'}\n"
                f"Wallet: {entry.wallet_address or 'N/A'}\n"
                f"Причина: {entry.reason[:30]}...\n"
                f"━━━━━━━━━━━━━━━\n\n"
            )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить в блеклист",
            callback_data="admin:add_to_blacklist",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="➖ Удалить из блеклиста",
            callback_data="admin:remove_from_blacklist",
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


@router.callback_query(lambda c: c.data == "admin:add_to_blacklist")
async def start_add_to_blacklist(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Start adding to blacklist."""
    await callback.message.edit_text(
        "➕ **Добавление в блеклист**\n\n"
        "Введите Telegram ID или BSC wallet address:",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin:blacklist",
            )
        )
        .as_markup(),
    )

    await state.set_state(BlacklistStates.waiting_for_identifier)
    await callback.answer()


@router.message(BlacklistStates.waiting_for_identifier)
async def process_blacklist_identifier(
    message: Message,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Process identifier for blacklist."""
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
                "❌ Неверный формат! Введите числовой Telegram ID или BSC адрес (0x...)."
            )
            return

    # Save to state
    await state.update_data(
        telegram_id=telegram_id,
        wallet_address=wallet_address,
    )

    await message.answer(
        "Введите причину блокировки:",
    )

    await state.set_state(BlacklistStates.waiting_for_reason)


@router.message(BlacklistStates.waiting_for_reason)
async def process_blacklist_reason(
    message: Message,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Process blacklist reason."""
    reason = message.text.strip()

    if len(reason) < 5:
        await message.answer(
            "❌ Причина слишком короткая! Минимум 5 символов."
        )
        return

    data = await state.get_data()
    telegram_id = data.get("telegram_id")
    wallet_address = data.get("wallet_address")

    blacklist_service = BlacklistService(session)

    try:
        entry = await blacklist_service.add_to_blacklist(
            telegram_id=telegram_id,
            wallet_address=wallet_address,
            reason=reason,
            added_by_admin_id=admin.id,
        )

        await session.commit()

        await message.answer(
            f"✅ **Добавлено в блеклист!**\n\n"
            f"ID: #{entry.id}\n"
            f"Telegram ID: {telegram_id or 'N/A'}\n"
            f"Wallet: {wallet_address or 'N/A'}\n"
            f"Причина: {reason}",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:blacklist",
                )
            )
            .as_markup(),
        )

    except Exception as e:
        logger.error(f"Error adding to blacklist: {e}")
        await message.answer(f"❌ Ошибка: {e}")

    await state.clear()


@router.callback_query(lambda c: c.data == "admin:remove_from_blacklist")
async def start_remove_from_blacklist(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Start removing from blacklist."""
    await callback.message.edit_text(
        "➖ **Удаление из блеклиста**\n\n"
        "Введите Telegram ID или wallet address для удаления:",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin:blacklist",
            )
        )
        .as_markup(),
    )

    await state.set_state(BlacklistStates.waiting_for_removal_identifier)
    await callback.answer()


@router.message(BlacklistStates.waiting_for_removal_identifier)
async def process_blacklist_removal(
    message: Message,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Process blacklist removal."""
    identifier = message.text.strip()

    telegram_id = None
    wallet_address = None

    if identifier.startswith("0x"):
        wallet_address = identifier.lower()
    else:
        try:
            telegram_id = int(identifier)
        except ValueError:
            await message.answer("❌ Неверный формат!")
            return

    blacklist_service = BlacklistService(session)

    success = await blacklist_service.remove_from_blacklist(
        telegram_id=telegram_id,
        wallet_address=wallet_address,
    )

    await session.commit()

    if success:
        await message.answer(
            f"✅ **Удалено из блеклиста!**\n\n"
            f"Пользователь снова может использовать бота.",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:blacklist",
                )
            )
            .as_markup(),
        )
    else:
        await message.answer(
            "❌ Запись не найдена в блеклисте.",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:blacklist",
                )
            )
            .as_markup(),
        )

    await state.clear()
