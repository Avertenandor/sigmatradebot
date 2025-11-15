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
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Handle deposit level selection with validation.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
        state: FSM state
    """
    # Extract level from callback data
    level = int(callback.data.split(":")[-1])

    # Validate purchase eligibility
    from app.services.deposit_validation_service import DepositValidationService
    
    validation_service = DepositValidationService(session)
    can_purchase, error_msg = await validation_service.can_purchase_level(
        user.id, level
    )

    if not can_purchase:
        await callback.answer(
            error_msg or "Нельзя купить этот уровень депозита",
            show_alert=True,
        )
        return

    # Get expected amount for this level
    from app.services.deposit_validation_service import DEPOSIT_LEVELS
    expected_amount = DEPOSIT_LEVELS[level]

    # Save level to state
    await state.update_data(level=level, expected_amount=str(expected_amount))

    # Ask for amount
    text = (
        f"📦 **Депозит уровня {level}**\n\n"
        f"💰 Сумма депозита: **{expected_amount} USDT**\n\n"
    )

    if level == 1:
        text += (
            "⚠️ Для уровня 1 действует ROI cap 500%\n"
            "(максимум можно заработать 5x от депозита)\n\n"
        )

    text += (
        "📝 **Следующий шаг:**\n"
        f"Отправьте {expected_amount} USDT на адрес кошелька проекта.\n\n"
        "После отправки введите hash транзакции:"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

    await state.set_state(DepositStates.waiting_for_tx_hash)


# NOTE: process_deposit_amount removed - now we go directly to tx_hash
# after selecting level, as amount is fixed per level (10/50/100/150/300 USDT)


@router.message(DepositStates.waiting_for_tx_hash)
async def process_tx_hash(
    message: Message,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Process transaction hash for deposit.

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

    # Get level and expected amount from state
    data = await state.get_data()
    level = data.get("level", 1)
    expected_amount_str = data.get("expected_amount")
    
    if expected_amount_str:
        expected_amount = Decimal(expected_amount_str)
    else:
        from app.services.deposit_validation_service import DEPOSIT_LEVELS
        expected_amount = DEPOSIT_LEVELS.get(level, Decimal("10"))

    # Validate purchase eligibility again (in case state was modified)
    from app.services.deposit_validation_service import DepositValidationService
    
    validation_service = DepositValidationService(session)
    can_purchase, error_msg = await validation_service.can_purchase_level(
        user.id, level
    )

    if not can_purchase:
        await message.answer(
            f"❌ {error_msg}\n\n"
            "Попробуйте выбрать другой уровень депозита."
        )
        await state.clear()
        return

    # Get system wallet address
    from app.config.settings import settings
    system_wallet = settings.system_wallet_address

    # Create deposit with pending status
    deposit_service = DepositService(session)
    deposit = await deposit_service.create_deposit(
        user_id=user.id,
        level=level,
        amount=expected_amount,
        tx_hash=tx_hash,
    )

    logger.info(
        "Deposit created with tx hash",
        extra={
            "deposit_id": deposit.id,
            "user_id": user.id,
            "level": level,
            "amount": str(expected_amount),
            "tx_hash": tx_hash,
        },
    )

    # Show deposit info with payment address
    text = (
        f"✅ **Депозит создан!**\n\n"
        f"📦 Уровень: {level}\n"
        f"💰 Сумма: {expected_amount} USDT\n"
        f"🆔 ID депозита: {deposit.id}\n"
        f"🔗 Hash транзакции: `{tx_hash}`\n\n"
    )

    if level == 1:
        roi_cap = expected_amount * Decimal("5.0")
        text += (
            f"💰 ROI Cap: {roi_cap} USDT "
            f"(максимум можно заработать)\n\n"
        )

    text += (
        f"📝 **Следующий шаг:**\n"
        f"Отправьте {expected_amount} USDT на адрес:\n"
        f"`{system_wallet}`\n\n"
        f"🌐 **Сеть:** BSC (BEP-20)\n"
        f"⏱ После отправки депозит будет автоматически активирован "
        f"после подтверждения транзакции (обычно 1-3 минуты).\n\n"
        f"📊 **Проверить транзакцию:**\n"
        f"https://bscscan.com/tx/{tx_hash}"
    )

    from bot.keyboards.reply import main_menu_reply_keyboard
    await message.answer(text, parse_mode="Markdown", reply_markup=main_menu_reply_keyboard())
    await state.clear()
