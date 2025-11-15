"""
Wallet management handler.

Allows admins to manage system and payout wallets.
"""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.wallet_admin_service import WalletAdminService
from bot.states.admin import WalletManagementStates

router = Router()


@router.callback_query(lambda c: c.data == "admin:wallets")
async def show_wallet_management(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Show wallet management menu."""
    from app.config import get_settings

    settings = get_settings()

    wallet_service = WalletAdminService(session)
    pending_requests = await wallet_service.get_pending_requests()

    text = (
        "💼 **Управление кошельками**\n\n"
        "**Текущие адреса:**\n"
        f"🏦 System: `{settings.system_wallet_address}`\n"
        f"💰 Payout: `{settings.payout_wallet_address}`\n\n"
    )

    if pending_requests:
        text += f"⏳ Ожидающих запросов: {len(pending_requests)}\n\n"

    builder = InlineKeyboardBuilder()

    if pending_requests:
        builder.row(
            InlineKeyboardButton(
                text=f"📋 Рассмотреть запросы ({len(pending_requests)})",
                callback_data="admin:wallet_requests",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🏦 Изменить System Wallet",
            callback_data="admin:change_system_wallet",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💰 Изменить Payout Wallet",
            callback_data="admin:change_payout_wallet",
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


@router.callback_query(lambda c: c.data == "admin:wallet_requests")
async def show_wallet_requests(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Show pending wallet change requests."""
    wallet_service = WalletAdminService(session)
    requests = await wallet_service.get_pending_requests()

    if not requests:
        await callback.answer("Нет ожидающих запросов", show_alert=True)
        return

    text = "📋 **Запросы на изменение кошельков**\n\n"

    builder = InlineKeyboardBuilder()

    for req in requests:
        text += (
            f"ID: #{req.id}\n"
            f"Тип: {req.wallet_type}\n"
            f"Новый адрес: `{req.new_address}`\n"
            f"Запросил: {req.requested_by_admin_id}\n"
            f"Причина: {req.reason}\n\n"
        )

        builder.row(
            InlineKeyboardButton(
                text=f"✅ Одобрить #{req.id}",
                callback_data=f"admin:approve_wallet:{req.id}",
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить #{req.id}",
                callback_data=f"admin:reject_wallet:{req.id}",
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin:wallets",
        )
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:approve_wallet:"))
async def approve_wallet_change(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Approve wallet change request."""
    request_id = int(callback.data.split(":")[-1])

    wallet_service = WalletAdminService(session)

    try:
        request = await wallet_service.approve_request(
            request_id=request_id,
            admin_id=admin.id,
            admin_notes="Approved via Telegram bot",
        )

        await session.commit()

        await callback.answer(
            f"✅ Запрос #{request_id} одобрен!\n"
            f"⚠️ Требуется обновить конфигурацию и перезапустить бота.",
            show_alert=True,
        )

        # Refresh display
        await show_wallet_requests(callback, session, admin)

    except ValueError as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("admin:reject_wallet:"))
async def reject_wallet_change(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Reject wallet change request."""
    request_id = int(callback.data.split(":")[-1])

    wallet_service = WalletAdminService(session)

    try:
        await wallet_service.reject_request(
            request_id=request_id,
            admin_id=admin.id,
            admin_notes="Rejected via Telegram bot",
        )

        await session.commit()

        await callback.answer(f"✅ Запрос #{request_id} отклонен", show_alert=True)

        # Refresh display
        await show_wallet_requests(callback, session, admin)

    except ValueError as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
