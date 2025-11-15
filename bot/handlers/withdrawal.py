"""
Withdrawal handler.

Handles withdrawal request flow.
"""

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import UserService
from app.services.withdrawal_service import WithdrawalService
from bot.keyboards.inline import main_menu_keyboard, withdrawal_keyboard
from bot.states.withdrawal import WithdrawalStates

router = Router()


@router.callback_query(F.data == "withdrawal:all")
async def withdraw_all(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Withdraw all available balance.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
        state: FSM state
    """
    # Check verification status (from TZ: withdrawals require verification)
    if not user.is_verified:
        await callback.answer(
            "❌ Для вывода средств необходимо пройти верификацию!\n\n"
            "Используйте кнопку '✅ Пройти верификацию' в настройках.",
            show_alert=True,
        )
        return
    
    # Get balance
    user_service = UserService(session)
    balance = await user_service.get_user_balance(user.id)

    if not balance or balance["available_balance"] == 0:
        await callback.answer(
            "❌ Недостаточно средств для вывода",
            show_alert=True,
        )
        return

    available = Decimal(str(balance["available_balance"]))

    # Check minimum
    min_amount = WithdrawalService.get_min_withdrawal_amount()
    if available < min_amount:
        await callback.answer(
            f"❌ Минимальная сумма вывода: {min_amount} USDT",
            show_alert=True,
        )
        return

    # Save amount and ask for password
    await state.update_data(amount=available)

    text = (
        f"💸 Вывод всех средств\n\n"
        f"Сумма: {available} USDT\n\n"
        f"Для подтверждения введите ваш финансовый пароль:"
    )

    await callback.message.edit_text(text)
    await callback.answer()

    await state.set_state(WithdrawalStates.waiting_for_financial_password)


@router.callback_query(F.data == "withdrawal:amount")
async def withdraw_amount(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Withdraw specific amount.

    Args:
        callback: Callback query
        state: FSM state
    """
    text = (
        f"💸 Вывод средств\n\n"
        f"Введите сумму вывода в USDT:\n\n"
        f"Минимальная сумма: "
        f"{WithdrawalService.get_min_withdrawal_amount()} USDT"
    )

    await callback.message.edit_text(text)
    await callback.answer()

    await state.set_state(WithdrawalStates.waiting_for_amount)


@router.message(WithdrawalStates.waiting_for_amount)
async def process_withdrawal_amount(
    message: Message,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Process withdrawal amount.

    Args:
        message: Telegram message
        session: Database session
        user: Current user
        state: FSM state
    """
    # Check verification status (from TZ: withdrawals require verification)
    if not user.is_verified:
        await message.answer(
            "❌ Для вывода средств необходимо пройти верификацию!\n\n"
            "Используйте кнопку '✅ Пройти верификацию' в настройках."
        )
        await state.clear()
        return
    
    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button
    if is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this
    
    try:
        amount = Decimal(message.text.strip())
    except (ValueError, ArithmeticError):
        await message.answer(
            "❌ Неверный формат суммы!\n\n"
            "Введите число (например: 100 или 100.50):"
        )
        return

    # Check minimum
    min_amount = WithdrawalService.get_min_withdrawal_amount()
    if amount < min_amount:
        await message.answer(
            f"❌ Сумма слишком маленькая!\n\n"
            f"Минимальная сумма: {min_amount} USDT\n"
            f"Попробуйте еще раз:"
        )
        return

    # Check balance
    user_service = UserService(session)
    balance = await user_service.get_user_balance(user.id)

    if not balance or Decimal(str(balance["available_balance"])) < amount:
        await message.answer(
            f"❌ Недостаточно средств!\n\n"
            f"Доступно: {balance['available_balance']:.2f} USDT\n"
            f"Попробуйте меньшую сумму:"
        )
        return

    # Save amount and ask for password
    await state.update_data(amount=amount)

    text = (
        f"💸 Вывод средств\n\n"
        f"Сумма: {amount} USDT\n\n"
        f"Для подтверждения введите ваш финансовый пароль:"
    )

    await message.answer(text)
    await state.set_state(WithdrawalStates.waiting_for_financial_password)


@router.message(WithdrawalStates.waiting_for_financial_password)
async def process_financial_password(
    message: Message,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Process financial password and create withdrawal.
    
    Args:
        message: Telegram message
        session: Database session
        user: Current user
        state: FSM state
    """
    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button
    if is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this
    password = message.text.strip()

    # Delete message with password
    await message.delete()

    # Verify password
    user_service = UserService(session)
    if not user_service.verify_financial_password(user, password):
        await message.answer(
            "❌ Неверный финансовый пароль!\n\n"
            "Попробуйте еще раз:"
        )
        return

    # Get amount from state
    data = await state.get_data()
    amount = data.get("amount")

    # Get balance
    balance = await user_service.get_user_balance(user.id)

    # Create withdrawal
    withdrawal_service = WithdrawalService(session)
    transaction, error = await withdrawal_service.request_withdrawal(
        user_id=user.id,
        amount=amount,
        available_balance=Decimal(str(balance["available_balance"])),
    )

    if error:
        from bot.keyboards.reply import main_menu_reply_keyboard
        await message.answer(
            f"❌ Ошибка создания заявки:\n{error}",
            reply_markup=main_menu_reply_keyboard(),
        )
        await state.clear()
        return

    logger.info(
        "Withdrawal requested",
        extra={
            "transaction_id": transaction.id,
            "user_id": user.id,
            "amount": str(amount),
        },
    )

    text = (
        f"✅ Заявка на вывод создана!\n\n"
        f"💰 Сумма: {amount} USDT\n"
        f"🆔 ID заявки: {transaction.id}\n"
        f"📍 Адрес: {user.masked_wallet}\n\n"
        f"⏳ Заявка находится на рассмотрении.\n"
        f"Обычно обработка занимает от 1 до 24 часов.\n\n"
        f"Вы получите уведомление после обработки."
    )

    from bot.keyboards.reply import main_menu_reply_keyboard
    await message.answer(text, reply_markup=main_menu_reply_keyboard())
    await state.clear()


@router.callback_query(F.data == "withdrawal:history")
async def show_withdrawal_history(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """
    Show withdrawal history.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
    """
    withdrawal_service = WithdrawalService(session)
    result = await withdrawal_service.get_user_withdrawals(
        user.id, page=1, limit=10
    )

    withdrawals = result["withdrawals"]

    if not withdrawals:
        text = "📜 История выводов пуста"
    else:
        text = "📜 История выводов:\n\n"
        for w in withdrawals:
            status_emoji = {
                "PENDING": "⏳",
                "CONFIRMED": "✅",
                "FAILED": "❌",
            }.get(w.status, "❓")

            text += (
                f"{status_emoji} {w.amount} USDT\n"
                f"📅 {w.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            )

            if w.tx_hash:
                text += f"🔗 Hash: `{w.tx_hash[:16]}...`\n"

            text += "\n"

    await callback.message.edit_text(
        text, reply_markup=withdrawal_keyboard()
    )
    await callback.answer()
