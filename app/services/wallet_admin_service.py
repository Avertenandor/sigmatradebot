"""
Wallet Admin Service.

Manages hot wallet changes with admin approval workflow.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_change_request import WalletChangeRequest
from app.repositories.wallet_change_request_repository import (
    WalletChangeRequestRepository,
)


class WalletAdminService:
    """
    Service for managing wallet change requests.

    Features:
    - System wallet changes
    - Payout wallet changes (with private key)
    - Dual admin approval (for security)
    - Audit logging
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize wallet admin service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = WalletChangeRequestRepository(session)

    async def request_system_wallet_change(
        self,
        new_address: str,
        requested_by_admin_id: int,
        reason: Optional[str] = None,
    ) -> WalletChangeRequest:
        """
        Request system wallet address change.

        Args:
            new_address: New wallet address
            requested_by_admin_id: Admin who requested
            reason: Change reason

        Returns:
            WalletChangeRequest instance

        Raises:
            ValueError: If pending request exists
        """
        # Check for pending requests
        pending = await self.repository.get_pending_requests()

        for req in pending:
            if req.wallet_type == "system":
                raise ValueError(
                    "Pending system wallet change request already exists"
                )

        # Create request
        request = await self.repository.create(
            wallet_type="system",
            new_address=new_address.lower(),
            requested_by_admin_id=requested_by_admin_id,
            reason=reason or "System wallet address update",
            status="pending",
        )

        logger.info(
            f"System wallet change requested: "
            f"new_address={new_address}, "
            f"admin_id={requested_by_admin_id}"
        )

        return request

    async def request_payout_wallet_change(
        self,
        new_address: str,
        new_private_key: str,
        requested_by_admin_id: int,
        reason: Optional[str] = None,
    ) -> WalletChangeRequest:
        """
        Request payout wallet change (with private key).

        Args:
            new_address: New wallet address
            new_private_key: New private key
            requested_by_admin_id: Admin who requested
            reason: Change reason

        Returns:
            WalletChangeRequest instance

        Raises:
            ValueError: If pending request exists
        """
        # Check for pending requests
        pending = await self.repository.get_pending_requests()

        for req in pending:
            if req.wallet_type == "payout":
                raise ValueError(
                    "Pending payout wallet change request already exists"
                )

        # Create request (private key will be encrypted in repository)
        request = await self.repository.create(
            wallet_type="payout",
            new_address=new_address.lower(),
            new_private_key=new_private_key,  # Encrypted in repo
            requested_by_admin_id=requested_by_admin_id,
            reason=reason or "Payout wallet update",
            status="pending",
        )

        logger.info(
            f"Payout wallet change requested: "
            f"new_address={new_address}, "
            f"admin_id={requested_by_admin_id}"
        )

        return request

    async def approve_request(
        self,
        request_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None,
    ) -> WalletChangeRequest:
        """
        Approve wallet change request.

        Args:
            request_id: Request ID
            admin_id: Admin ID who approved
            admin_notes: Approval notes

        Returns:
            Updated WalletChangeRequest

        Raises:
            ValueError: If request not found, not pending, or same admin
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Wallet change request not found")

        if request.status != "pending":
            raise ValueError(
                f"Request is not pending (status: {request.status})"
            )

        # Prevent self-approval (security)
        if request.requested_by_admin_id == admin_id:
            raise ValueError(
                "Admin cannot approve their own wallet change request"
            )

        # Update request
        request = await self.repository.update(
            request.id,
            status="approved",
            approved_by_admin_id=admin_id,
            approved_at=datetime.utcnow(),
            admin_notes=admin_notes,
        )

        logger.info(
            f"Wallet change request approved: "
            f"request_id={request_id}, "
            f"admin_id={admin_id}, "
            f"wallet_type={request.wallet_type}"
        )

        return request

    async def reject_request(
        self,
        request_id: int,
        admin_id: int,
        admin_notes: Optional[str] = None,
    ) -> WalletChangeRequest:
        """
        Reject wallet change request.

        Args:
            request_id: Request ID
            admin_id: Admin ID who rejected
            admin_notes: Rejection reason

        Returns:
            Updated WalletChangeRequest
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Wallet change request not found")

        if request.status != "pending":
            raise ValueError(
                f"Request is not pending (status: {request.status})"
            )

        # Update request
        request = await self.repository.update(
            request.id,
            status="rejected",
            approved_by_admin_id=admin_id,
            approved_at=datetime.utcnow(),
            admin_notes=admin_notes or "Request rejected",
        )

        logger.info(
            f"Wallet change request rejected: "
            f"request_id={request_id}, "
            f"admin_id={admin_id}"
        )

        return request

    async def mark_as_applied(
        self,
        request_id: int,
    ) -> WalletChangeRequest:
        """
        Mark wallet change as applied.

        Args:
            request_id: Request ID

        Returns:
            Updated WalletChangeRequest
        """
        request = await self.repository.get_by_id(request_id)

        if not request:
            raise ValueError("Wallet change request not found")

        if request.status != "approved":
            raise ValueError(
                f"Request is not approved (status: {request.status})"
            )

        # Mark as applied
        request = await self.repository.update(
            request.id,
            applied_at=datetime.utcnow(),
        )

        logger.info(
            f"Wallet change applied: "
            f"request_id={request_id}, "
            f"wallet_type={request.wallet_type}"
        )

        return request

    async def get_pending_requests(self) -> list[WalletChangeRequest]:
        """
        Get all pending wallet change requests.

        Returns:
            List of pending requests
        """
        return await self.repository.get_pending_requests()

    async def get_request_history(
        self,
        limit: int = 20,
    ) -> list[WalletChangeRequest]:
        """
        Get wallet change request history.

        Args:
            limit: Maximum requests to return

        Returns:
            List of requests
        """
        return await self.repository.get_recent_requests(limit=limit)

    async def count_pending(self) -> int:
        """
        Count pending wallet change requests.

        Returns:
            Number of pending requests
        """
        return await self.repository.count_pending()
