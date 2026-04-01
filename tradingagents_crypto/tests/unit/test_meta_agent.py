"""
Unit tests for Meta-Agent and Analyst Coordinator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tradingagents_crypto.graph.nodes.meta_agent import meta_agent_node, Task
from tradingagents_crypto.graph.nodes.analyst_coordinator import (
    analyst_coordinator,
    _safe_analyst_run,
)


class TestMetaAgentNode:
    """Tests for meta_agent_node."""

    @pytest.mark.asyncio
    async def test_meta_agent_decomposes_task(self):
        """Test that meta_agent decomposes request into tasks."""
        state = {
            "user_request": "Analyze BTC and ETH",
            "symbol": "BTC",
        }
        result = await meta_agent_node(state)

        assert result["status"] == "dispatched"
        assert len(result["tasks"]) == 4  # BTC, ETH, SOL, Macro
        assert any(t["type"] == "btc_analysis" for t in result["tasks"])
        assert any(t["type"] == "eth_analysis" for t in result["tasks"])
        assert any(t["type"] == "sol_analysis" for t in result["tasks"])
        assert any(t["type"] == "macro_analysis" for t in result["tasks"])

    @pytest.mark.asyncio
    async def test_meta_agent_sets_priority(self):
        """Test that meta_agent sets correct priorities."""
        state = {"user_request": "test", "symbol": "ETH"}
        result = await meta_agent_node(state)

        btc_task = next(t for t in result["tasks"] if t["type"] == "btc_analysis")
        sol_task = next(t for t in result["tasks"] if t["type"] == "sol_analysis")

        assert btc_task["priority"] == 1  # High priority
        assert sol_task["priority"] == 2  # Medium priority

    @pytest.mark.asyncio
    async def test_meta_agent_uses_symbol_from_state(self):
        """Test that meta_agent uses symbol from state."""
        state = {"user_request": "test", "symbol": "ETH"}
        result = await meta_agent_node(state)

        btc_task = next(t for t in result["tasks"] if t["type"] == "btc_analysis")
        assert btc_task["symbol"] == "ETH"


class TestAnalystCoordinator:
    """Tests for analyst_coordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_requires_llm(self):
        """Test that coordinator raises if llm not provided."""
        state = {"tasks": [], "llm": None}
        with pytest.raises(ValueError, match="llm not provided"):
            await analyst_coordinator(state)

    @pytest.mark.asyncio
    async def test_coordinator_with_empty_tasks(self):
        """Test coordinator with no tasks."""
        llm = MagicMock()
        state = {"tasks": [], "llm": llm}
        result = await analyst_coordinator(state)

        assert result["status"] == "completed"
        assert result["analyst_results"] == {}

    @pytest.mark.asyncio
    async def test_coordinator_parallel_execution(self):
        """Test that coordinator executes high priority analysts in parallel."""
        llm = MagicMock()

        # Mock the agent factory to return mock analysts
        mock_analyst1 = AsyncMock()
        mock_analyst1.arun = AsyncMock(return_value={"result": "BTC analysis"})

        mock_analyst2 = AsyncMock()
        mock_analyst2.arun = AsyncMock(return_value={"result": "ETH analysis"})

        with patch(
            "tradingagents_crypto.graph.nodes.analyst_coordinator.AgentFactory.create_analyst"
        ) as mock_create:
            # Return different mocks based on type
            def create_side_effect(agent_type, llm):
                if agent_type == "btc_analysis":
                    return mock_analyst1
                return mock_analyst2

            mock_create.side_effect = create_side_effect

            state = {
                "tasks": [
                    {"type": "btc_analysis", "priority": 1, "symbol": "BTC"},
                    {"type": "eth_analysis", "priority": 1, "symbol": "ETH"},
                ],
                "llm": llm,
            }
            result = await analyst_coordinator(state)

            # Both should be called
            assert mock_analyst1.arun.called
            assert mock_analyst2.arun.called


class TestSafeAnalystRun:
    """Tests for _safe_analyst_run helper."""

    @pytest.mark.asyncio
    async def test_safe_run_passes_input_data(self):
        """Test that _safe_analyst_run passes correct input data."""
        mock_analyst = AsyncMock()
        mock_analyst.arun = AsyncMock(return_value={"result": "ok"})

        task = {"type": "btc_analysis", "symbol": "BTC", "trade_date": "2026-04-01"}
        await _safe_analyst_run(mock_analyst, task)

        mock_analyst.arun.assert_called_once_with({
            "symbol": "BTC",
            "trade_date": "2026-04-01",
        })

    @pytest.mark.asyncio
    async def test_safe_run_returns_result(self):
        """Test that _safe_analyst_run returns analyst result."""
        mock_analyst = AsyncMock()
        mock_analyst.arun = AsyncMock(return_value={"analysis": "bullish"})

        task = {"type": "btc_analysis", "symbol": "BTC"}
        result = await _safe_analyst_run(mock_analyst, task)

        assert result["analysis"] == "bullish"
