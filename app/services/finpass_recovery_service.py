"""
Financial Password Recovery Service.

Manages financial password recovery requests with admin approval workflow.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_password_recovery import FinancialPasswordRecovery
from app.repositories.financial_password_recovery_repository import (
    FinancialPasswordRecoveryRepository,
)


class FinpassRecoveryService:
    """
    Service for managing financial password recovery.

    Features:
    - User request submission
    - Admin approval/rejection
    - Earnings blocking during recovery
    - Auto-unblock after verification
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize finpass recovery service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = FinancialPasswordRecoveryRepository(session)

    async def create_recovery_request(
        self,
        user_id: int,
        reason: Optional[str] = None,
    ) -> FinancialPasswordRecovery:
        """
        Create financial password recovery request.

        Args:
            user_id: User ID
            reason: Recovery reason

        Returns:
            FinancialPasswordRecovery instance

        Raises:
            ValueError: If active request already exists
        """
        # Check for existing pending request
        existing = await self.repository.find_pending_by_user(user_id)

        if existing:
            raise ValueError(
                "Active recovery request already exists for this user"
            )

        # Create request
        request = await self.repository.create(
            {
                "user_id": user_id,
                "reason": reason or "User requested password recovery",
                "status": "pending",
            }
        )

        logger.info(
            f"Financial password recovery request created: "
            f"user_id={user_id}, request_id={request.id}"
        )

        return request

    async def approve_request(
        self,
        request_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None,
    ) -> FinancialPasswordRecovery:
        """
        Approve recovery request.

        Args:
            request_id: Request ID
            admin_id: Admin ID who approved
            admin_notes: Admin notes

        Returns:
            Updated FinancialPasswordRecovery

        Raises:
            ValueError: If request not found or not pending
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Recovery request not found")

        if request.status != "pending":
            raise ValueError(
                f"Request is not pending (status: {request.status})"
            )

        # Update request
        request.status = "approved"
        request.reviewed_by_admin_id = admin_id
        request.reviewed_at = datetime.utcnow()
        request.admin_notes = admin_notes

        await self.repository.update(request)

        logger.info(
            f"Financial password recovery approved: "
            f"request_id={request_id}, admin_id={admin_id}"
        )

        return request

    async def reject_request(
        self,
        request_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None,
    ) -> FinancialPasswordRecovery:
        """
        Reject recovery request.

        Args:
            request_id: Request ID
            admin_id: Admin ID who rejected
            admin_notes: Rejection reason

        Returns:
            Updated FinancialPasswordRecovery

        Raises:
            ValueError: If request not found or not pending
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Recovery request not found")

        if request.status != "pending":
            raise ValueError(
                f"Request is not pending (status: {request.status})"
            )

        # Update request
        request.status = "rejected"
        request.reviewed_by_admin_id = admin_id
        request.reviewed_at = datetime.utcnow()
        request.admin_notes = admin_notes or "Request rejected"

        await self.repository.update(request)

        logger.info(
            f"Financial password recovery rejected: "
            f"request_id={request_id}, admin_id={admin_id}"
        )

        return request

    async def mark_as_verified(
        self,
        request_id: int,
    ) -> FinancialPasswordRecovery:
        """
        Mark recovery request as verified (user used new password).

        Args:
            request_id: Request ID

        Returns:
            Updated FinancialPasswordRecovery

        Raises:
            ValueError: If request not found or not approved
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Recovery request not found")

        if request.status != "approved":
            raise ValueError(
                f"Request is not approved (status: {request.status})"
            )

        # Mark as verified
        request.verified_at = datetime.utcnow()

        await self.repository.update(request)

        logger.info(
            f"Financial password recovery verified: "
            f"request_id={request_id}"
        )

        return request

    async def get_pending_by_user(
        self,
        user_id: int,
    ) -> Optional[FinancialPasswordRecovery]:
        """
        Get pending recovery request for user.

        Args:
            user_id: User ID

        Returns:
            FinancialPasswordRecovery or None
        """
        return await self.repository.find_pending_by_user(user_id)

    async def get_all_pending(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialPasswordRecovery]:
        """
        Get all pending recovery requests.

        Args:
            limit: Maximum requests to return
            offset: Offset for pagination

        Returns:
            List of pending requests
        """
        return await self.repository.get_pending_requests(
            limit=limit,
            offset=offset,
        )

    async def get_user_requests(
        self,
        user_id: int,
        limit: int = 10,
    ) -> list[FinancialPasswordRecovery]:
        """
        Get all recovery requests for user.

        Args:
            user_id: User ID
            limit: Maximum requests to return

        Returns:
            List of requests
        """
        return await self.repository.get_by_user_id(
            user_id=user_id,
            limit=limit,
        )

    async def has_active_recovery(
        self,
        user_id: int,
    ) -> bool:
        """
        Check if user has active recovery (approved but not verified).

        Args:
            user_id: User ID

        Returns:
            True if active recovery exists
        """
        request = await self.repository.find_active_recovery(user_id)
        return request is not None

    async def count_pending(self) -> int:
        """
        Count pending recovery requests.

        Returns:
            Number of pending requests
        """
        return await self.repository.count_pending()
