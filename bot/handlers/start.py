"""
Start handler.

Handles /start command and user registration.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import UserService
from bot.keyboards.inline import main_menu_keyboard
from bot.states.registration import RegistrationStates

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    user: User | None,
    state: FSMContext,
) -> None:
    """
    Handle /start command.

    Args:
        message: Telegram message
        session: Database session
        user: Current user (if registered)
        state: FSM state
    """
    # Check if already registered
    if user:
        await message.answer(
            f"Добро пожаловать обратно, {user.username or 'пользователь'}!\n\n"
            f"Ваш баланс: {user.balance} USDT\n"
            f"Используйте меню ниже для навигации.",
            reply_markup=main_menu_keyboard(),
        )
        return

    # Start registration
    await message.answer(
        "👋 Добро пожаловать в SigmaTrade!\n\n"
        "Для начала работы необходимо пройти регистрацию.\n\n"
        "📝 Шаг 1: Введите ваш BSC (BEP-20) адрес кошелька\n"
        "Формат: 0x...\n\n"
        "❗️ Внимание: убедитесь, что адрес указан правильно!"
    )

    await state.set_state(RegistrationStates.waiting_for_wallet)


@router.message(RegistrationStates.waiting_for_wallet)
async def process_wallet(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Process wallet address.

    Args:
        message: Telegram message
        session: Database session
        state: FSM state
    """
    wallet_address = message.text.strip()

    # Validate wallet format (0x + 40 hex chars)
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        await message.answer(
            "❌ Неверный формат адреса!\n\n"
            "BSC адрес должен начинаться с '0x' и содержать 42 символа.\n"
            "Попробуйте еще раз:"
        )
        return

    # Check if wallet already registered
    user_service = UserService(session)
    existing = await user_service.get_by_wallet(wallet_address)

    if existing:
        await message.answer(
            "❌ Этот кошелек уже зарегистрирован!\n\n"
            "Используйте другой адрес:"
        )
        return

    # Save wallet to state
    await state.update_data(wallet_address=wallet_address)

    # Ask for financial password
    await message.answer(
        "✅ Адрес кошелька принят!\n\n"
        "📝 Шаг 2: Создайте финансовый пароль\n"
        "Этот пароль будет использоваться для подтверждения выводов.\n\n"
        "Требования:\n"
        "• Минимум 6 символов\n"
        "• Не используйте простые пароли\n\n"
        "Введите пароль:"
    )

    await state.set_state(
        RegistrationStates.waiting_for_financial_password
    )


@router.message(RegistrationStates.waiting_for_financial_password)
async def process_financial_password(
    message: Message, state: FSMContext
) -> None:
    """
    Process financial password.

    Args:
        message: Telegram message
        state: FSM state
    """
    password = message.text.strip()

    # Validate password
    if len(password) < 6:
        await message.answer(
            "❌ Пароль слишком короткий!\n\n"
            "Минимальная длина: 6 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    # Delete message with password
    await message.delete()

    # Save password to state
    await state.update_data(financial_password=password)

    # Ask for confirmation
    await message.answer(
        "✅ Пароль принят!\n\n"
        "📝 Шаг 3: Подтвердите пароль\n"
        "Введите пароль еще раз:"
    )

    await state.set_state(
        RegistrationStates.waiting_for_password_confirmation
    )


@router.message(RegistrationStates.waiting_for_password_confirmation)
async def process_password_confirmation(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    """
    Process password confirmation and complete registration.

    Args:
        message: Telegram message
        session: Database session
        state: FSM state
    """
    confirmation = message.text.strip()

    # Delete message with password
    await message.delete()

    # Get data from state
    data = await state.get_data()
    password = data.get("financial_password")

    # Check if passwords match
    if confirmation != password:
        await message.answer(
            "❌ Пароли не совпадают!\n\n"
            "Введите пароль еще раз:"
        )
        await state.set_state(
            RegistrationStates.waiting_for_financial_password
        )
        return

    # Register user
    wallet_address = data.get("wallet_address")
    user_service = UserService(session)

    user, error = await user_service.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        wallet_address=wallet_address,
        financial_password=password,
        referrer_telegram_id=None,  # TODO: Handle referrals
    )

    if error:
        await message.answer(
            f"❌ Ошибка регистрации:\n{error}\n\n"
            "Попробуйте начать заново: /start"
        )
        await state.clear()
        return

    # Registration successful
    logger.info(
        "User registered successfully",
        extra={
            "user_id": user.id,
            "telegram_id": message.from_user.id,
        },
    )

    await message.answer(
        "🎉 Регистрация завершена!\n\n"
        f"Ваш ID: {user.id}\n"
        f"Кошелек: {user.masked_wallet}\n\n"
        "Добро пожаловать в SigmaTrade! 🚀",
        reply_markup=main_menu_keyboard(),
    )

    await state.clear()
