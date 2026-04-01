"""
Unit tests for manual approval workflow.
"""
import pytest
import asyncio
from tradingagents_crypto.trading.approval.workflow import (
    ApprovalWorkflow,
    ApprovalRequest,
    ApprovalStatus,
)


class TestApprovalWorkflow:
    """Tests for ApprovalWorkflow."""

    @pytest.fixture
    def workflow(self):
        """Create an ApprovalWorkflow instance."""
        return ApprovalWorkflow(min_size_threshold=0.05)

    def test_requires_approval_above_threshold(self, workflow):
        """Test that size above threshold requires approval."""
        assert workflow.requires_approval(0.05) is True
        assert workflow.requires_approval(0.10) is True
        assert workflow.requires_approval(0.50) is True

    def test_requires_approval_below_threshold(self, workflow):
        """Test that size below threshold doesn't require approval."""
        assert workflow.requires_approval(0.01) is False
        assert workflow.requires_approval(0.04) is False

    def test_requires_approval_at_exact_threshold(self, workflow):
        """Test boundary condition at exact threshold."""
        assert workflow.requires_approval(0.05) is True

    @pytest.mark.asyncio
    async def test_submit_and_get_status(self, workflow):
        """Test submitting a request and checking status."""
        request = ApprovalRequest(
            decision_id="dec_001",
            action="long",
            symbol="BTC",
            size_pct=0.10,
            leverage=5,
            reason="Strong buy signal",
            risk_warnings=["High volatility"],
        )
        await workflow.submit(request)

        status = await workflow.get_status("dec_001")
        assert status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_approve(self, workflow):
        """Test approving a request."""
        request = ApprovalRequest(
            decision_id="dec_002",
            action="short",
            symbol="ETH",
            size_pct=0.20,
            leverage=3,
            reason="Funding rate high",
            risk_warnings=[],
        )
        await workflow.submit(request)

        result = await workflow.approve("dec_002", comments="Looks good")
        assert result is True

        status = await workflow.get_status("dec_002")
        assert status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_reject(self, workflow):
        """Test rejecting a request."""
        request = ApprovalRequest(
            decision_id="dec_003",
            action="long",
            symbol="SOL",
            size_pct=0.30,
            leverage=10,
            reason="Risky",
            risk_warnings=["High leverage"],
        )
        await workflow.submit(request)

        result = await workflow.reject("dec_003", comments="Too risky")
        assert result is True

        status = await workflow.get_status("dec_003")
        assert status == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_skip(self, workflow):
        """Test skipping approval."""
        request = ApprovalRequest(
            decision_id="dec_004",
            action="close",
            symbol="BTC",
            size_pct=0.05,
            leverage=1,
            reason="Stop loss",
            risk_warnings=[],
        )
        await workflow.submit(request)

        result = await workflow.skip("dec_004")
        assert result is True

        status = await workflow.get_status("dec_004")
        assert status == ApprovalStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_approve_nonexistent(self, workflow):
        """Test approving non-existent decision returns False."""
        result = await workflow.approve("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_reject_nonexistent(self, workflow):
        """Test rejecting non-existent decision returns False."""
        result = await workflow.reject("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_pending(self, workflow):
        """Test listing pending requests."""
        for i in range(3):
            request = ApprovalRequest(
                decision_id=f"dec_{i}",
                action="long",
                symbol="BTC",
                size_pct=0.10,
                leverage=5,
                reason="Test",
                risk_warnings=[],
            )
            await workflow.submit(request)

        pending = await workflow.list_pending()
        assert len(pending) == 3

    @pytest.mark.asyncio
    async def test_list_pending_excludes_approved(self, workflow):
        """Test that list_pending excludes approved items."""
        for i in range(3):
            request = ApprovalRequest(
                decision_id=f"dec_{i}",
                action="long",
                symbol="BTC",
                size_pct=0.10,
                leverage=5,
                reason="Test",
                risk_warnings=[],
            )
            await workflow.submit(request)

        await workflow.approve("dec_0")
        pending = await workflow.list_pending()
        assert len(pending) == 2


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.SKIPPED.value == "skipped"

    def test_status_is_string(self):
        """Test that status values are strings."""
        for status in ApprovalStatus:
            assert isinstance(status.value, str)


class TestApprovalRequest:
    """Tests for ApprovalRequest dataclass."""

    def test_creation(self):
        """Test creating an ApprovalRequest."""
        request = ApprovalRequest(
            decision_id="dec_001",
            action="long",
            symbol="BTC",
            size_pct=0.10,
            leverage=5,
            reason="Test",
            risk_warnings=["Warning1"],
        )
        assert request.decision_id == "dec_001"
        assert request.status == ApprovalStatus.PENDING
        assert request.risk_warnings == ["Warning1"]

    def test_default_status(self):
        """Test that default status is PENDING."""
        request = ApprovalRequest(
            decision_id="dec_001",
            action="hold",
            symbol="ETH",
            size_pct=0.0,
            leverage=1,
            reason="No action",
            risk_warnings=[],
        )
        assert request.status == ApprovalStatus.PENDING

    def test_comments_default_empty(self):
        """Test that comments default to empty string."""
        request = ApprovalRequest(
            decision_id="dec_001",
            action="close",
            symbol="BTC",
            size_pct=0.0,
            leverage=1,
            reason="Close",
            risk_warnings=[],
        )
        assert request.approver_comments == ""
