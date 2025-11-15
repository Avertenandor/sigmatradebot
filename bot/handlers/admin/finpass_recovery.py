"""
Financial password recovery admin handler.

Allows admins to approve/reject finpass recovery requests.
"""

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.finpass_recovery_service import FinpassRecoveryService
from app.services.user_service import UserService

router = Router()


@router.callback_query(lambda c: c.data == "admin:finpass_recovery")
async def show_recovery_requests(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Show pending finpass recovery requests."""
    recovery_service = FinpassRecoveryService(session)
    requests = await recovery_service.get_all_pending()

    if not requests:
        await callback.message.edit_text(
            "📋 **Запросы на восстановление пароля**\n\n"
            "Нет ожидающих запросов.",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:panel",
                )
            )
            .as_markup(),
        )
        await callback.answer()
        return

    text = f"🔐 **Запросы на восстановление пароля**\n\nВсего: {len(requests)}\n\n"

    builder = InlineKeyboardBuilder()

    for req in requests[:10]:  # Show max 10
        user_service = UserService(session)
        user = await user_service.get_user_by_id(req.user_id)

        text += (
            f"━━━━━━━━━━━━━━━\n"
            f"ID: #{req.id}\n"
            f"Пользователь: {user.username if user else 'N/A'} (ID: {req.user_id})\n"
            f"Причина: {req.reason[:50]}...\n"
            f"Создан: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

        builder.row(
            InlineKeyboardButton(
                text=f"✅ Одобрить #{req.id}",
                callback_data=f"admin:approve_recovery:{req.id}",
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить #{req.id}",
                callback_data=f"admin:reject_recovery:{req.id}",
            ),
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


@router.callback_query(lambda c: c.data.startswith("admin:approve_recovery:"))
async def approve_recovery(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Approve finpass recovery request."""
    request_id = int(callback.data.split(":")[-1])

    recovery_service = FinpassRecoveryService(session)
    user_service = UserService(session)

    try:
        request = await recovery_service.approve_request(
            request_id=request_id,
            admin_id=admin.id,
            admin_notes="Approved via Telegram bot",
        )

        # Generate new financial password
        import secrets
        import string

        new_password = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(12)
        )

        # Update user's financial password
        user = await user_service.get_user_by_id(request.user_id)

        if user:
            import bcrypt

            hashed = bcrypt.hashpw(
                new_password.encode(),
                bcrypt.gensalt(rounds=12),
            )

            user.financial_password_hash = hashed.decode()

            # Block earnings until verification
            user.earnings_blocked = True

            await session.commit()

            # Send new password to user
            try:
                await callback.bot.send_message(
                    user.telegram_id,
                    f"✅ **Ваш запрос на восстановление пароля одобрен!**\n\n"
                    f"Новый финансовый пароль: `{new_password}`\n\n"
                    f"⚠️ **Важно:**\n"
                    f"• Сохраните этот пароль в надежном месте\n"
                    f"• Ваши выплаты заблокированы до первого использования пароля\n"
                    f"• После первого успешного вывода блокировка будет снята\n\n"
                    f"Используйте раздел 'Вывод' для проверки нового пароля.",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Failed to send password to user: {e}")

        await callback.answer(
            f"✅ Запрос #{request_id} одобрен!\n"
            f"Новый пароль отправлен пользователю.",
            show_alert=True,
        )

        # Refresh display
        await show_recovery_requests(callback, session, admin)

    except Exception as e:
        logger.error(f"Error approving recovery: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("admin:reject_recovery:"))
async def reject_recovery(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Reject finpass recovery request."""
    request_id = int(callback.data.split(":")[-1])

    recovery_service = FinpassRecoveryService(session)

    try:
        request = await recovery_service.reject_request(
            request_id=request_id,
            admin_id=admin.id,
            admin_notes="Rejected via Telegram bot",
        )

        await session.commit()

        # Notify user
        try:
            await callback.bot.send_message(
                request.user_id,
                f"❌ **Ваш запрос на восстановление пароля отклонен**\n\n"
                f"ID запроса: #{request_id}\n\n"
                f"Если у вас есть вопросы, обратитесь в поддержку.",
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")

        await callback.answer(f"✅ Запрос #{request_id} отклонен", show_alert=True)

        # Refresh display
        await show_recovery_requests(callback, session, admin)

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
