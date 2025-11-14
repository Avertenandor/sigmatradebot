"""
Admin management handler.

Allows super admins to promote/demote other admins.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.admin_service import AdminService
from bot.states.admin import AdminManagementStates

router = Router()


@router.callback_query(lambda c: c.data == "admin:management")
async def show_admin_management(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """
    Show admin management menu.

    Args:
        callback: Callback query
        session: Database session
        admin: Current admin
    """
    # Only super_admin can manage admins
    if admin.role != "super_admin":
        await callback.answer(
            "❌ Только супер админ может управлять администраторами!",
            show_alert=True,
        )
        return

    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()

    text = "👥 **Управление администраторами**\n\n"

    for adm in admins:
        role_emoji = {
            "super_admin": "👑",
            "extended_admin": "⭐",
            "admin": "👤",
        }.get(adm.role, "👤")

        text += (
            f"{role_emoji} `{adm.telegram_id}` - {adm.username or 'N/A'}\n"
            f"   Роль: {adm.role}\n"
            f"   Активен: {'✅' if adm.is_active else '❌'}\n\n"
        )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить админа",
            callback_data="admin:add_admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔽 Понизить админа",
            callback_data="admin:demote_admin",
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


@router.callback_query(lambda c: c.data == "admin:add_admin")
async def start_add_admin(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Start adding new admin."""
    if admin.role != "super_admin":
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await callback.message.edit_text(
        "➕ **Добавление администратора**\n\n"
        "Введите Telegram ID пользователя:",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin:management",
            )
        )
        .as_markup(),
    )

    await state.set_state(AdminManagementStates.waiting_for_telegram_id)
    await callback.answer()


@router.message(AdminManagementStates.waiting_for_telegram_id)
async def process_telegram_id(
    message: Message,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Process telegram ID for new admin."""
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Неверный формат! Введите числовой Telegram ID."
        )
        return

    # Save to state
    await state.update_data(telegram_id=telegram_id)

    # Ask for role
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="👤 Admin",
            callback_data="admin:role:admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⭐ Extended Admin",
            callback_data="admin:role:extended_admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin:management",
        )
    )

    await message.answer(
        f"Выберите роль для пользователя `{telegram_id}`:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )

    await state.set_state(AdminManagementStates.waiting_for_role)


@router.callback_query(
    AdminManagementStates.waiting_for_role,
    lambda c: c.data.startswith("admin:role:"),
)
async def process_role(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Process role selection."""
    role = callback.data.split(":")[-1]
    data = await state.get_data()
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        await callback.answer("❌ Ошибка: Telegram ID не найден!", show_alert=True)
        await state.clear()
        return

    # Create admin
    admin_service = AdminService(session)

    try:
        new_admin = await admin_service.create_admin(
            telegram_id=telegram_id,
            role=role,
            username=None,  # Will be updated on first interaction
        )

        await session.commit()

        await callback.message.edit_text(
            f"✅ **Администратор добавлен!**\n\n"
            f"Telegram ID: `{new_admin.telegram_id}`\n"
            f"Роль: {new_admin.role}\n\n"
            f"Пользователь может войти в админ панель используя /admin",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:management",
                )
            )
            .as_markup(),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при создании администратора: {e}",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="admin:management",
                )
            )
            .as_markup(),
        )

    await state.clear()
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:demote_admin")
async def start_demote_admin(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
    state: FSMContext,
) -> None:
    """Start demoting admin."""
    if admin.role != "super_admin":
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()

    # Filter out super_admin and current admin
    demotable = [
        a for a in admins if a.role != "super_admin" and a.id != admin.id
    ]

    if not demotable:
        await callback.answer(
            "Нет администраторов для понижения!",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    for adm in demotable:
        builder.row(
            InlineKeyboardButton(
                text=f"🔽 {adm.username or adm.telegram_id} ({adm.role})",
                callback_data=f"admin:demote:{adm.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin:management",
        )
    )

    await callback.message.edit_text(
        "🔽 **Понижение администратора**\n\n"
        "Выберите администратора для удаления:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:demote:"))
async def confirm_demote(
    callback: CallbackQuery,
    session: AsyncSession,
    admin: Admin,
) -> None:
    """Confirm admin demotion."""
    admin_id = int(callback.data.split(":")[-1])

    admin_service = AdminService(session)
    target_admin = await admin_service.get_admin_by_id(admin_id)

    if not target_admin:
        await callback.answer("❌ Админ не найден!", show_alert=True)
        return

    # Delete admin
    await admin_service.delete_admin(admin_id)
    await session.commit()

    await callback.message.edit_text(
        f"✅ **Администратор удален!**\n\n"
        f"Пользователь `{target_admin.telegram_id}` больше не имеет прав администратора.",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="admin:management",
            )
        )
        .as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()
