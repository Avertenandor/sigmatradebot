"""
Deposit handler.

Handles deposit creation flow.
"""

from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.deposit_service import DepositService
from bot.keyboards.inline import deposit_keyboard, main_menu_keyboard
from bot.states.deposit import DepositStates

router = Router()


@router.callback_query(F.data.startswith("deposit:level:"))
async def select_deposit_level(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Handle deposit level selection.

    Args:
        callback: Callback query
        state: FSM state
    """
    # Extract level from callback data
    level = int(callback.data.split(":")[-1])

    # Save level to state
    await state.update_data(level=level)

    # Ask for amount
    text = (
        f"📦 Депозит уровня {level}\n\n"
        f"Введите сумму депозита в USDT:\n\n"
    )

    if level == 1:
        text += (
            "⚠️ Для уровня 1 действует ROI cap 500%\n"
            "(максимум можно заработать 5x от депозита)\n\n"
        )

    text += "Минимальная сумма: 10 USDT"

    await callback.message.edit_text(text)
    await callback.answer()

    await state.set_state(DepositStates.waiting_for_amount)


@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(
    message: Message,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Process deposit amount.

    Args:
        message: Telegram message
        session: Database session
        user: Current user
        state: FSM state
    """
    try:
        amount = Decimal(message.text.strip())
    except (ValueError, ArithmeticError):
        await message.answer(
            "❌ Неверный формат суммы!\n\n"
            "Введите число (например: 100 или 100.50):"
        )
        return

    # Validate amount
    if amount < 10:
        await message.answer(
            "❌ Сумма слишком маленькая!\n\n"
            "Минимальная сумма: 10 USDT\n"
            "Попробуйте еще раз:"
        )
        return

    # Get level from state
    data = await state.get_data()
    level = data.get("level", 1)

    # Create deposit
    deposit_service = DepositService(session)
    deposit = await deposit_service.create_deposit(
        user_id=user.id,
        level=level,
        amount=amount,
    )

    logger.info(
        "Deposit created",
        extra={
            "deposit_id": deposit.id,
            "user_id": user.id,
            "level": level,
            "amount": str(amount),
        },
    )

    # Calculate ROI cap info
    roi_info = ""
    if level == 1:
        roi_cap = amount * Decimal("5.0")
        roi_info = (
            f"\n\n💰 ROI Cap: {roi_cap} USDT "
            f"(максимум можно заработать)"
        )

    # Show deposit info
    text = (
        f"✅ Депозит создан!\n\n"
        f"📦 Уровень: {level}\n"
        f"💰 Сумма: {amount} USDT\n"
        f"🆔 ID депозита: {deposit.id}\n"
        f"{roi_info}\n\n"
        f"📝 Следующий шаг:\n"
        f"Отправьте {amount} USDT на адрес:\n"
        f"`{deposit.payment_address or 'адрес будет предоставлен'}`\n\n"
        f"После отправки введите hash транзакции:"
    )

    await message.answer(text)
    await state.set_state(DepositStates.waiting_for_tx_hash)
    await state.update_data(deposit_id=deposit.id)


@router.message(DepositStates.waiting_for_tx_hash)
async def process_tx_hash(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Process transaction hash.

    Args:
        message: Telegram message
        session: Database session
        state: FSM state
    """
    tx_hash = message.text.strip()

    # Basic validation
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        await message.answer(
            "❌ Неверный формат hash!\n\n"
            "Transaction hash должен начинаться с '0x' "
            "и содержать 66 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    # Get deposit ID from state
    data = await state.get_data()
    deposit_id = data.get("deposit_id")

    # Update deposit with tx_hash
    deposit_service = DepositService(session)
    deposit = await deposit_service.deposit_repo.update(
        deposit_id, tx_hash=tx_hash
    )

    logger.info(
        "Deposit tx_hash updated",
        extra={
            "deposit_id": deposit_id,
            "tx_hash": tx_hash,
        },
    )

    text = (
        f"✅ Transaction hash принят!\n\n"
        f"🔍 Ваш депозит находится на проверке.\n"
        f"После подтверждения в блокчейне (обычно 1-5 минут)\n"
        f"депозит будет автоматически активирован.\n\n"
        f"Вы получите уведомление о подтверждении."
    )

    await message.answer(text, reply_markup=main_menu_keyboard())
    await state.clear()
