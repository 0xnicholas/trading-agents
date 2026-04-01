"""
Manual approval workflow for trading decisions.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ApprovalStatus(Enum):
    """Approval status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass
class ApprovalRequest:
    """A trading decision awaiting approval."""
    decision_id: str
    action: str  # long, short, close, hold
    symbol: str
    size_pct: float
    leverage: int
    reason: str
    risk_warnings: list[str]
    status: ApprovalStatus = ApprovalStatus.PENDING
    submitted_at: float | None = None
    decided_at: float | None = None
    approver_comments: str = ""


class ApprovalWorkflow:
    """Manual approval workflow for high-value trades."""

    def __init__(self, min_size_threshold: float = 0.05):
        """Initialize approval workflow.

        Args:
            min_size_threshold: Minimum position size % requiring approval
        """
        self.min_size_threshold = min_size_threshold
        self._pending: dict[str, ApprovalRequest] = {}
        self._lock = asyncio.Lock()

    def requires_approval(self, size_pct: float) -> bool:
        """Check if a trade requires manual approval.

        Args:
            size_pct: Position size as decimal (0.0-1.0)

        Returns:
            True if approval is required
        """
        return size_pct >= self.min_size_threshold

    async def submit(self, request: ApprovalRequest) -> str:
        """Submit a decision for approval.

        Args:
            request: ApprovalRequest to submit

        Returns:
            decision_id for tracking
        """
        async with self._lock:
            request.submitted_at = asyncio.get_event_loop().time()
            self._pending[request.decision_id] = request
        return request.decision_id

    async def approve(self, decision_id: str, comments: str = "") -> bool:
        """Approve a pending decision.

        Args:
            decision_id: ID of the decision to approve
            comments: Optional approver comments

        Returns:
            True if approved, False if not found
        """
        async with self._lock:
            if decision_id not in self._pending:
                return False
            req = self._pending[decision_id]
            req.status = ApprovalStatus.APPROVED
            req.decided_at = asyncio.get_event_loop().time()
            req.approver_comments = comments
            return True

    async def reject(self, decision_id: str, comments: str = "") -> bool:
        """Reject a pending decision.

        Args:
            decision_id: ID of the decision to reject
            comments: Reason for rejection

        Returns:
            True if rejected, False if not found
        """
        async with self._lock:
            if decision_id not in self._pending:
                return False
            req = self._pending[decision_id]
            req.status = ApprovalStatus.REJECTED
            req.decided_at = asyncio.get_event_loop().time()
            req.approver_comments = comments
            return True

    async def skip(self, decision_id: str) -> bool:
        """Skip approval (auto-approve or bypass).

        Args:
            decision_id: ID of the decision to skip

        Returns:
            True if skipped, False if not found
        """
        async with self._lock:
            if decision_id not in self._pending:
                return False
            req = self._pending[decision_id]
            req.status = ApprovalStatus.SKIPPED
            req.decided_at = asyncio.get_event_loop().time()
            return True

    async def get_status(self, decision_id: str) -> ApprovalStatus | None:
        """Get the approval status of a decision.

        Args:
            decision_id: ID of the decision

        Returns:
            ApprovalStatus if found, None otherwise
        """
        async with self._lock:
            req = self._pending.get(decision_id)
            return req.status if req else None

    async def list_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests."""
        async with self._lock:
            return [
                req for req in self._pending.values()
                if req.status == ApprovalStatus.PENDING
            ]
