"""
Instructions handler.

Provides deposit instructions and BSCScan links.
"""

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

router = Router()


@router.callback_query(lambda c: c.data == "menu:instructions")
async def show_instructions(
    callback: CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """
    Show deposit instructions.

    Args:
        callback: Callback query
        session: Database session
        user: Current user
    """
    from app.config import get_settings

    settings = get_settings()

    instructions_text = (
        "📋 **Инструкция по пополнению депозита**\n\n"
        "1️⃣ **Откройте ваш BSC кошелек** (Trust Wallet, MetaMask и т.д.)\n\n"
        "2️⃣ **Отправьте USDT (BEP-20)** на следующий адрес:\n"
        f"`{settings.system_wallet_address}`\n\n"
        "3️⃣ **Сумма депозита:**\n"
        f"   • Уровень 1: {settings.deposit_level_1} USDT\n"
        f"   • Уровень 2: {settings.deposit_level_2} USDT\n"
        f"   • Уровень 3: {settings.deposit_level_3} USDT\n"
        f"   • Уровень 4: {settings.deposit_level_4} USDT\n"
        f"   • Уровень 5: {settings.deposit_level_5} USDT\n\n"
        "4️⃣ **Дождитесь подтверждения** (обычно 1-3 минуты)\n\n"
        "5️⃣ **Депозит активируется автоматически** после 12 подтверждений блоков\n\n"
        "⚠️ **Важно:**\n"
        "• Отправляйте только USDT (BEP-20) на BSC сети!\n"
        "• Не отправляйте токены других сетей (ERC-20, TRC-20)\n"
        "• Убедитесь, что сумма точно совпадает с уровнем депозита\n"
        "• Сохраните хеш транзакции для отслеживания\n\n"
        "📊 **Проверить транзакцию:**\n"
        f"BSCScan: https://bscscan.com/address/{settings.system_wallet_address}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💰 Создать депозит",
            callback_data="menu:deposit",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔍 Проверить транзакцию",
            url=f"https://bscscan.com/address/{settings.system_wallet_address}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="menu:main",
        )
    )

    await callback.message.edit_text(
        instructions_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(lambda m: m.text and "инструкц" in m.text.lower())
async def cmd_instructions(
    message: Message,
    session: AsyncSession,
    user: User | None,
) -> None:
    """
    Handle instructions command via text.

    Args:
        message: Telegram message
        session: Database session
        user: Current user
    """
    if not user:
        await message.answer(
            "❌ Сначала необходимо зарегистрироваться!\n"
            "Используйте /start для начала."
        )
        return

    from app.config import get_settings

    settings = get_settings()

    instructions_text = (
        "📋 **Инструкция по пополнению депозита**\n\n"
        "1️⃣ Откройте ваш BSC кошелек\n"
        "2️⃣ Отправьте USDT (BEP-20) на адрес:\n"
        f"`{settings.system_wallet_address}`\n\n"
        "3️⃣ Выберите уровень депозита:\n"
        f"   • Уровень 1: {settings.deposit_level_1} USDT\n"
        f"   • Уровень 2: {settings.deposit_level_2} USDT\n"
        f"   • Уровень 3: {settings.deposit_level_3} USDT\n"
        f"   • Уровень 4: {settings.deposit_level_4} USDT\n"
        f"   • Уровень 5: {settings.deposit_level_5} USDT\n\n"
        "4️⃣ Дождитесь автоматического подтверждения\n\n"
        "Используйте /deposit для создания депозита"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💰 Создать депозит",
            callback_data="menu:deposit",
        )
    )

    await message.answer(
        instructions_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
