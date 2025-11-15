"""
Verification handler.

Handles user verification with financial password generation.
"""

import secrets
import string
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import UserService
from bot.keyboards.inline import main_menu_keyboard, settings_keyboard
from bot.keyboards.reply import main_menu_reply_keyboard


router = Router(name="verification")


def generate_financial_password(length: int = 8) -> str:
    """
    Generate random financial password.
    
    Args:
        length: Password length (default 8)
        
    Returns:
        Random password string
    """
    # Use digits and uppercase letters for better readability
    alphabet = string.digits + string.ascii_uppercase
    # Exclude confusing characters: 0, O, I, 1
    alphabet = alphabet.replace("0", "").replace("O", "").replace("I", "").replace("1", "")
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


@router.message(F.text == "✅ Пройти верификацию")
@router.callback_query(F.data == "verification:start")
async def start_verification(
    event: Message | CallbackQuery,
    session: AsyncSession,
    user: User,
    state: FSMContext,
) -> None:
    """
    Start verification process - generate financial password.
    
    Args:
        event: Message or callback query
        session: Database session
        user: Current user
        state: FSM state
    """
    # Clear any active FSM state
    await state.clear()
    
    # Check if already verified
    if user.is_verified:
        message_text = (
            "✅ Вы уже прошли верификацию!\n\n"
            "Ваш финансовый пароль уже установлен. "
            "Если вы забыли пароль, обратитесь в поддержку."
        )
        
        if isinstance(event, Message):
            await event.answer(
                message_text,
                reply_markup=main_menu_reply_keyboard(),
            )
        else:
            await event.message.edit_text(
                message_text,
                reply_markup=settings_keyboard(),
            )
            await event.answer()
        return
    
    # Generate financial password
    financial_password = generate_financial_password(8)
    
    # Hash and save password
    user_service = UserService(session)
    
    # Import bcrypt hashing
    import bcrypt
    password_hash = bcrypt.hashpw(
        financial_password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
    
    # Update user
    await user_service.update_profile(
        user.id,
        financial_password=password_hash,
        is_verified=True,
    )
    
    logger.info(
        "User verified with generated password",
        extra={
            "user_id": user.id,
            "telegram_id": user.telegram_id,
        },
    )
    
    # Show password ONCE with warning
    password_message = (
        "🔐 **Финансовый пароль сгенерирован!**\n\n"
        f"**Ваш пароль:** `{financial_password}`\n\n"
        "⚠️ **ВАЖНО:**\n"
        "• Сохраните этот пароль в безопасном месте\n"
        "• Он нужен для подтверждения финансовых операций\n"
        "• Пароль больше НЕ будет показан\n"
        "• При утере пароля обратитесь в поддержку\n\n"
        "✅ Верификация завершена!"
    )
    
    if isinstance(event, Message):
        await event.answer(
            password_message,
            parse_mode="Markdown",
            reply_markup=main_menu_reply_keyboard(),
        )
    else:
        await event.message.edit_text(
            password_message,
            parse_mode="Markdown",
            reply_markup=settings_keyboard(),
        )
        await event.answer("✅ Верификация завершена!")


@router.callback_query(F.data == "verification:show_password")
async def show_password_reminder(
    callback: CallbackQuery,
) -> None:
    """
    Show reminder that password cannot be shown again.
    
    Args:
        callback: Callback query
    """
    await callback.answer(
        "❌ Финансовый пароль хранится только у вас.\n"
        "При утере пароля обратитесь в поддержку.",
        show_alert=True,
    )

