"""
Notification service (+ PART5 multimedia support).

Sends notifications to users via Telegram.
"""

from typing import Any, Dict, List, Optional

from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.failed_notification import FailedNotification
from app.repositories.failed_notification_repository import (
    FailedNotificationRepository,
)
from app.repositories.admin_repository import AdminRepository
from app.repositories.support_ticket_repository import SupportTicketRepository


class NotificationService:
    """
    Notification service.

    Handles Telegram notifications with multimedia support (PART5).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize notification service."""
        self.session = session
        self.failed_repo = FailedNotificationRepository(session)
        self.admin_repo = AdminRepository(session)
        self.ticket_repo = SupportTicketRepository(session)

    async def send_notification(
        self,
        bot: Bot,
        user_telegram_id: int,
        message: str,
        critical: bool = False,
    ) -> bool:
        """
        Send text notification.

        Args:
            bot: Bot instance
            user_telegram_id: Telegram user ID
            message: Message text
            critical: Mark as critical

        Returns:
            True if sent successfully
        """
        try:
            await bot.send_message(
                chat_id=user_telegram_id, text=message
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to send notification: {e}",
                extra={"user_id": user_telegram_id},
            )

            # Save to failed notifications (PART5)
            await self._save_failed_notification(
                user_telegram_id,
                "text_message",
                message,
                str(e),
                critical,
            )
            return False

    async def send_photo(
        self,
        bot: Bot,
        user_telegram_id: int,
        file_id: str,
        caption: Optional[str] = None,
    ) -> bool:
        """
        Send photo notification (PART5 multimedia).

        Args:
            bot: Bot instance
            user_telegram_id: Telegram user ID
            file_id: Telegram file ID
            caption: Photo caption

        Returns:
            True if sent successfully
        """
        try:
            await bot.send_photo(
                chat_id=user_telegram_id,
                photo=file_id,
                caption=caption,
            )
            return True
        except Exception as e:
            await self._save_failed_notification(
                user_telegram_id,
                "photo",
                caption or "",
                str(e),
                metadata={"file_id": file_id},
            )
            return False

    async def _save_failed_notification(
        self,
        user_telegram_id: int,
        notification_type: str,
        message: str,
        error: str,
        critical: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FailedNotification:
        """Save failed notification for retry (PART5)."""
        return await self.failed_repo.create(
            user_telegram_id=user_telegram_id,
            notification_type=notification_type,
            message=message,
            last_error=error,
            critical=critical,
            metadata=metadata,
        )

    async def notify_admins_new_ticket(
        self, bot: Bot, ticket_id: int
    ) -> None:
        """
        Notify all admins about new support ticket.

        Args:
            bot: Bot instance
            ticket_id: Support ticket ID
        """
        # Get ticket details
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            logger.error(
                "Ticket not found for admin notification",
                extra={"ticket_id": ticket_id},
            )
            return

        # Get all admins
        all_admins = await self.admin_repo.find_by()

        if not all_admins:
            logger.warning("No admins found to notify about new ticket")
            return

        # Build notification message
        message = f"""
🆕 **Новое обращение в поддержку**

📋 Тикет #{ticket_id}
👤 Пользователь ID: {ticket.user_id}
📂 Категория: {ticket.category}
🕐 Время создания: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Перейдите в админ-панель для обработки.
        """.strip()

        # Send to all admins
        for admin in all_admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=message,
                    parse_mode="Markdown",
                )
                logger.info(
                    "Admin notified about new ticket",
                    extra={
                        "admin_id": admin.id,
                        "ticket_id": ticket_id,
                    },
                )
            except Exception as e:
                logger.error(
                    f"Failed to notify admin about ticket: {e}",
                    extra={
                        "admin_id": admin.id,
                        "ticket_id": ticket_id,
                    },
                )
                await self._save_failed_notification(
                    admin.telegram_id,
                    "admin_notification",
                    message,
                    str(e),
                    critical=True,
                )
