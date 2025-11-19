"""
Financial password recovery admin handler.

Allows admins to approve/reject finpass recovery requests.
"""

import re
from typing import Any

from aiogram import F, Router
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.finpass_recovery_service import FinpassRecoveryService
from app.services.user_service import UserService
from bot.keyboards.reply import admin_keyboard

router = Router()


@router.message(F.text == "🔑 Восстановление пароля")
async def show_recovery_requests(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Show pending finpass recovery requests."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    recovery_service = FinpassRecoveryService(session)
    user_service = UserService(session)
    requests = await recovery_service.get_all_pending()

    if not requests:
        await message.answer(
            "🔑 **Запросы на восстановление пароля**\n\n"
            "Нет ожидающих запросов.",
            parse_mode="Markdown",
            reply_markup=admin_keyboard(),
        )
        return

    text = (
        f"🔑 **Запросы на восстановление пароля**\n\nВсего: {len(requests)}\n\n"
    )

    display_requests = requests[:10]

    for req in display_requests:
        user = await user_service.get_user_by_id(req.user_id)
        if user:
            username = user.username or str(user.telegram_id)
            user_label = f"{username} (ID: {user.id})"
        else:
            user_label = f"ID: {req.user_id}"
        reason_preview = (
            req.reason if len(req.reason) <= 80 else f"{req.reason[:77]}..."
        )

        text += (
            f"─────────────────────────────\n"
            f"ID: #{req.id}\n"
            f"Пользователь: {user_label}\n"
            f"Причина: {reason_preview}\n"
            f"Создан: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    if len(requests) > len(display_requests):
        text += (
            "─────────────────────────────\n"
            f"И еще {len(requests) - len(display_requests)} запросов не показаны в этом списке.\n\n"
        )

    text += (
        "Для одобрения заявки введите: **одобрить восстановление <ID>**\n"
        "Для отклонения заявки введите: **отклонить восстановление <ID>**\n"
        "Пример: `одобрить восстановление 123` или `отклонить восстановление 123`"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=admin_keyboard(),
    )


@router.message(F.text.regexp(r"^одобрить восстановление\s+(\d+)$", flags=0))
async def approve_recovery(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Approve finpass recovery request."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    # Extract request ID from message text
    match = re.match(
        r"^одобрить восстановление\s+(\d+)$", message.text.strip(), re.IGNORECASE
    )
    if not match:
        await message.answer(
            "❌ Неверный формат. Используйте: `одобрить восстановление <ID>`",
            reply_markup=admin_keyboard(),
        )
        return

    request_id = int(match.group(1))

    # Get admin
    from app.repositories.admin_repository import AdminRepository
    
    admin_repo = AdminRepository(session)
    admin = await admin_repo.get_by(telegram_id=message.from_user.id)
    
    if not admin:
        await message.answer(
            "❌ Администратор не найден",
            reply_markup=admin_keyboard(),
        )
        return

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

        new_password = "".join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(12)
        )

        # Update user's financial password
        user = await user_service.get_user_by_id(request.user_id)

        if not user:
            raise ValueError("User not found for this recovery request")

        import bcrypt

        hashed = bcrypt.hashpw(
            new_password.encode(),
            bcrypt.gensalt(rounds=12),
        )

        user.financial_password = hashed.decode()
        user.earnings_blocked = True

        await message.bot.send_message(
            user.telegram_id,
            f"✅ **Ваш запрос на "
            f"восстановление пароля одобрен!**\n\n"
            f"Новый финансовый пароль: "
            f"`{new_password}`\n\n"
            f"⚠️ **Важно:**\n"
            f"• Сохраните этот пароль в надёжном месте\n"
            f"• Ваши выплаты заблокированы "
            f"до первого использования пароля\n"
            f"• После первого успешного вывода блокировка будет снята\n\n"
            f"Используйте раздел 'Вывод' для проверки нового пароля.",
            parse_mode="Markdown",
        )

        await recovery_service.mark_sent(
            request_id=request.id,
            admin_id=admin.id,
            admin_notes="Password sent to user",
        )

        await session.commit()

        await message.answer(
            f"✅ Запрос #{request_id} одобрен!\n"
            f"Новый пароль отправлен пользователю.",
            reply_markup=admin_keyboard(),
        )

        # Refresh display
        await show_recovery_requests(message, session, **data)

    except Exception as e:
        await session.rollback()
        logger.error(f"Error approving recovery: {e}")
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=admin_keyboard(),
        )


@router.message(F.text.regexp(r"^отклонить восстановление\s+(\d+)$", flags=0))
async def reject_recovery(
    message: Message,
    session: AsyncSession,
    **data: Any,
) -> None:
    """Reject finpass recovery request."""
    is_admin = data.get("is_admin", False)
    if not is_admin:
        await message.answer("❌ Эта функция доступна только администраторам")
        return

    # Extract request ID from message text
    match = re.match(
        r"^отклонить восстановление\s+(\d+)$", message.text.strip(), re.IGNORECASE
    )
    if not match:
        await message.answer(
            "❌ Неверный формат. Используйте: `отклонить восстановление <ID>`",
            reply_markup=admin_keyboard(),
        )
        return

    request_id = int(match.group(1))

    # Get admin
    from app.repositories.admin_repository import AdminRepository
    
    admin_repo = AdminRepository(session)
    admin = await admin_repo.get_by(telegram_id=message.from_user.id)
    
    if not admin:
        await message.answer(
            "❌ Администратор не найден",
            reply_markup=admin_keyboard(),
        )
        return

    recovery_service = FinpassRecoveryService(session)
    user_service = UserService(session)

    try:
        request = await recovery_service.reject_request(
            request_id=request_id,
            admin_id=admin.id,
            admin_notes="Rejected via Telegram bot",
        )

        user = await user_service.get_user_by_id(request.user_id)

        await session.commit()

        if user:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"❌ **Ваш запрос на "
                    f"восстановление пароля отклонён**\n\n"
                    f"ID запроса: #{request_id}\n\n"
                    f"Если у вас есть вопросы, обратитесь в поддержку.",
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")

        await message.answer(
            f"✅ Запрос #{request_id} отклонён",
            reply_markup=admin_keyboard(),
        )

        # Refresh display
        await show_recovery_requests(message, session, **data)

    except Exception as e:
        await session.rollback()
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=admin_keyboard(),
        )
