"""
Admin management handler.

Allows super admins to promote/demote other admins.
"""

from aiogram import Router
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
            "тЭМ ╨в╨╛╨╗╤М╨║╨╛ ╤Б╤Г╨┐╨╡╤А ╨░╨┤╨╝╨╕╨╜ ╨╝╨╛╨╢╨╡╤В"
                "╤Г╨┐╤А╨░╨▓╨╗╤П╤В╤М ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░╨╝╨╕!",
            show_alert=True,
        )
        return

    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()

    text = "ЁЯСе **╨г╨┐╤А╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░╨╝╨╕**\n\n"

    for adm in admins:
        role_emoji = {
            "super_admin": "ЁЯСС",
            "extended_admin": "тнР",
            "admin": "ЁЯСд",
        }.get(adm.role, "ЁЯСд")

        text += (
            f"{role_emoji} `{adm.telegram_id}` - {adm.username or 'N/A'}\n"
            f"   ╨а╨╛╨╗╤М: {adm.role}\n"
            f"   ╨Р╨║╤В╨╕╨▓╨╡╨╜: {'тЬЕ' if adm.is_active else 'тЭМ'}\n\n"
        )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="тЮХ ╨Ф╨╛╨▒╨░╨▓╨╕╤В╤М ╨░╨┤╨╝╨╕╨╜╨░",
            callback_data="admin:add_admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ЁЯФ╜ ╨Я╨╛╨╜╨╕╨╖╨╕╤В╤М ╨░╨┤╨╝╨╕╨╜╨░",
            callback_data="admin:demote_admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="тЧАя╕П ╨Э╨░╨╖╨░╨┤",
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
        await callback.answer(
            "тЭМ ╨Ф╨╛╤Б╤В╤Г╨┐ ╨╖╨░╨┐╤А╨╡╤Й╨╡╨╜!", show_alert=True
        )
        return

    await callback.message.edit_text(
        "тЮХ **╨Ф╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░**\n\n"
        "╨Т╨▓╨╡╨┤╨╕╤В╨╡ Telegram ID ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П:",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="тЭМ ╨Ю╤В╨╝╨╡╨╜╨░",
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
    # Check if message is a menu button - if so, clear state and ignore
    from bot.utils.menu_buttons import is_menu_button

    if message.text and is_menu_button(message.text):
        await state.clear()
        return  # Let menu handlers process this

    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "тЭМ ╨Э╨╡╨▓╨╡╤А╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В! ╨Т╨▓╨╡╨┤╨╕╤В╨╡"
                "╤З╨╕╤Б╨╗╨╛╨▓╨╛╨╣ Telegram ID."
        )
        return

    # Save to state
    await state.update_data(telegram_id=telegram_id)

    # Ask for role
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="ЁЯСд Admin",
            callback_data="admin:role:admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="тнР Extended Admin",
            callback_data="admin:role:extended_admin",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="тЭМ ╨Ю╤В╨╝╨╡╨╜╨░",
            callback_data="admin:management",
        )
    )

    await message.answer(
        "╨Т╤Л╨▒╨╡╤А╨╕╤В╨╡ ╤А╨╛╨╗╤М ╨┤╨╗╤П ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П"
            "`{telegram_id}`:",
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
        await callback.answer(
            "тЭМ ╨Ю╤И╨╕╨▒╨║╨░: Telegram ID ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜!", show_alert=True
        )
        await state.clear()
        return

    # Create admin
    admin_service = AdminService(session)

    try:
        new_admin, master_key, error = await admin_service.create_admin(
            telegram_id=telegram_id,
            role=role,
            created_by=admin.id,
            username=None,  # Will be updated on first interaction
        )

        if error or not new_admin:
            await callback.message.edit_text(
                f"❌ **Ошибка при создании администратора!**\n\n{error}",
                parse_mode="Markdown",
            )
            await state.clear()
            return

        await session.commit()

        await callback.message.edit_text(
            f"тЬЕ **╨Р╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜!**\n\n"
            f"Telegram ID: `{new_admin.telegram_id}`\n"
            f"╨а╨╛╨╗╤М: {new_admin.role}\n\n"
            f"╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╝╨╛╨╢╨╡╤В ╨▓╨╛╨╣╤В╨╕ ╨▓"
                "╨░╨┤╨╝╨╕╨╜ ╨┐╨░╨╜╨╡╨╗╤М ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╤П /admin",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="тЧАя╕П ╨Э╨░╨╖╨░╨┤",
                    callback_data="admin:management",
                )
            )
            .as_markup(),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        await callback.message.edit_text(
            "тЭМ ╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╕"
                "╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░: {e}",
            reply_markup=InlineKeyboardBuilder()
            .row(
                InlineKeyboardButton(
                    text="тЧАя╕П ╨Э╨░╨╖╨░╨┤",
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
        await callback.answer(
            "тЭМ ╨Ф╨╛╤Б╤В╤Г╨┐ ╨╖╨░╨┐╤А╨╡╤Й╨╡╨╜!", show_alert=True
        )
        return

    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()

    # Filter out super_admin and current admin
    demotable = [
        a for a in admins if a.role != "super_admin" and a.id != admin.id
    ]

    if not demotable:
        await callback.answer(
            "╨Э╨╡╤В ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨╛╨▓ ╨┤╨╗╤П ╨┐╨╛╨╜╨╕╨╢╨╡╨╜╨╕╤П!",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    for adm in demotable:
        builder.row(
            InlineKeyboardButton(
                text=f"ЁЯФ╜ {adm.username or adm.telegram_id} ({adm.role})",
                callback_data=f"admin:demote:{adm.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="тЭМ ╨Ю╤В╨╝╨╡╨╜╨░",
            callback_data="admin:management",
        )
    )

    await callback.message.edit_text(
        "ЁЯФ╜ **╨Я╨╛╨╜╨╕╨╢╨╡╨╜╨╕╨╡ ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░**\n\n"
        "╨Т╤Л╨▒╨╡╤А╨╕╤В╨╡ ╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░ ╨┤╨╗╤П"
            "╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П:",
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
        await callback.answer(
            "тЭМ ╨Р╨┤╨╝╨╕╨╜ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜!", show_alert=True
        )
        return

    # Delete admin
    await admin_service.delete_admin(admin_id)
    await session.commit()

    await callback.message.edit_text(
        f"тЬЕ **╨Р╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А ╤Г╨┤╨░╨╗╨╡╨╜!**\n\n"
        f"╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М `{target_admin.telegram_id}`"
            "╨▒╨╛╨╗╤М╤И╨╡ ╨╜╨╡ ╨╕╨╝╨╡╨╡╤В ╨┐╤А╨░╨▓"
                "╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А╨░.",
        reply_markup=InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="тЧАя╕П ╨Э╨░╨╖╨░╨┤",
                callback_data="admin:management",
            )
        )
        .as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()
