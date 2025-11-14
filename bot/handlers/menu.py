"""
Menu handler.

Handles main menu navigation.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from bot.keyboards.inline import (
    deposit_keyboard,
    main_menu_keyboard,
    referral_keyboard,
    support_keyboard,
    withdrawal_keyboard,
)

router = Router()


@router.message(F.text == "📊 Главное меню")
@router.callback_query(F.data == "menu:main")
async def show_main_menu(
    event: Message | CallbackQuery,
    user: User,
) -> None:
    """
    Show main menu.

    Args:
        event: Message or callback query
        user: Current user
    """
    text = (
        f"👤 Пользователь: {user.username or 'Аноним'}\n"
        f"💰 Баланс: {user.balance} USDT\n\n"
        f"Выберите действие:"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=main_menu_keyboard())
    else:
        await event.message.edit_text(
            text, reply_markup=main_menu_keyboard()
        )
        await event.answer()


@router.callback_query(F.data == "menu:balance")
async def show_balance(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """
    Show user balance.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
    """
    user_service = UserService(session)
    balance = await user_service.get_user_balance(user.id)

    if not balance:
        await callback.answer("Ошибка получения баланса", show_alert=True)
        return

    text = (
        f"💰 Ваш баланс:\n\n"
        f"Общий: {balance['total_balance']:.2f} USDT\n"
        f"Доступно: {balance['available_balance']:.2f} USDT\n"
        f"В ожидании: {balance['pending_earnings']:.2f} USDT\n\n"
        f"📊 Статистика:\n"
        f"Депозиты: {balance['total_deposits']:.2f} USDT\n"
        f"Выводы: {balance['total_withdrawals']:.2f} USDT\n"
        f"Заработано: {balance['total_earnings']:.2f} USDT"
    )

    await callback.message.edit_text(
        text, reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:history")
async def show_history(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """
    Show transaction history.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
    """
    tx_service = TransactionService(session)
    recent = await tx_service.get_recent_transactions(user.id, limit=10)

    if not recent:
        text = "📜 История транзакций пуста"
    else:
        text = "📜 Последние транзакции:\n\n"
        for tx in recent:
            status_emoji = {
                "PENDING": "⏳",
                "CONFIRMED": "✅",
                "FAILED": "❌",
            }.get(tx.status.name, "❓")

            text += (
                f"{status_emoji} {tx.description}\n"
                f"💰 {tx.amount} USDT\n"
                f"📅 {tx.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )

    await callback.message.edit_text(
        text, reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:deposit")
async def show_deposit_menu(callback: CallbackQuery) -> None:
    """
    Show deposit menu.

    Args:
        callback: Callback query
    """
    text = (
        "💰 Депозит\n\n"
        "Выберите уровень депозита:\n\n"
        "📦 Уровень 1: ROI cap 500%\n"
        "📦 Уровень 2-5: Без ROI cap"
    )

    await callback.message.edit_text(
        text, reply_markup=deposit_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:withdrawal")
async def show_withdrawal_menu(callback: CallbackQuery) -> None:
    """
    Show withdrawal menu.

    Args:
        callback: Callback query
    """
    text = (
        "💸 Вывод средств\n\n"
        "Минимальная сумма: 5 USDT\n"
        "Комиссия сети: ~0.1-0.5 USDT\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text, reply_markup=withdrawal_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:referral")
async def show_referral_menu(
    callback: CallbackQuery, user: User
) -> None:
    """
    Show referral menu.

    Args:
        callback: Callback query
        user: Current user
    """
    # Generate referral link
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref{user.telegram_id}"

    text = (
        f"👥 Реферальная программа\n\n"
        f"Ваша реферальная ссылка:\n"
        f"`{ref_link}`\n\n"
        f"💰 Вознаграждения:\n"
        f"• Уровень 1: 3%\n"
        f"• Уровень 2: 2%\n"
        f"• Уровень 3: 5%\n\n"
        f"Приглашайте друзей и зарабатывайте!"
    )

    await callback.message.edit_text(
        text,
        reply_markup=referral_keyboard(user.telegram_id),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:support")
async def show_support_menu(callback: CallbackQuery) -> None:
    """
    Show support menu.

    Args:
        callback: Callback query
    """
    text = (
        "💬 Поддержка\n\n"
        "Наша команда готова помочь вам 24/7!\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text, reply_markup=support_keyboard()
    )
    await callback.answer()
