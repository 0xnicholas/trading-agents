"""
Unit tests for parallel analyst execution.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from tradingagents_crypto.graph.nodes.parallel_analysts import (
    run_analysts_parallel,
    SyncAnalystAdapter,
)


class TestRunAnalystsParallel:
    """Tests for run_analysts_parallel."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test that analysts are executed in parallel."""
        analyst1 = AsyncMock()
        analyst1.arun = AsyncMock(return_value={"result": "BTC analysis"})
        analyst1.config = MagicMock()
        analyst1.config.name = "btc"

        analyst2 = AsyncMock()
        analyst2.arun = AsyncMock(return_value={"result": "ETH analysis"})
        analyst2.config = MagicMock()
        analyst2.config.name = "eth"

        results = await run_analysts_parallel(
            [analyst1, analyst2],
            {"symbol": "BTC"},
        )

        assert len(results) == 2
        analyst1.arun.assert_called_once()
        analyst2.arun.assert_called_once()
        assert results[0]["result"] == "BTC analysis"
        assert results[1]["result"] == "ETH analysis"

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeout errors are caught and returned as error dict."""
        analyst = AsyncMock()
        analyst.arun = AsyncMock(side_effect=asyncio.TimeoutError)
        analyst.config = MagicMock()
        analyst.config.name = "slow"

        results = await run_analysts_parallel(
            [analyst],
            {"symbol": "BTC"},
            timeout=0.1,
        )

        assert "error" in results[0]

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test that exceptions are caught and returned as error dict."""
        analyst = AsyncMock()
        analyst.arun = AsyncMock(side_effect=ValueError("Test error"))
        analyst.config = MagicMock()
        analyst.config.name = "error"

        results = await run_analysts_parallel(
            [analyst],
            {"symbol": "BTC"},
        )

        assert "error" in results[0]
        assert "Test error" in results[0]["error"]

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self):
        """Test handling mixed success and failure."""
        success_analyst = AsyncMock()
        success_analyst.arun = AsyncMock(return_value={"result": "ok"})
        success_analyst.config = MagicMock()
        success_analyst.config.name = "success"

        failure_analyst = AsyncMock()
        failure_analyst.arun = AsyncMock(side_effect=ValueError("fail"))
        failure_analyst.config = MagicMock()
        failure_analyst.config.name = "failure"

        results = await run_analysts_parallel(
            [success_analyst, failure_analyst],
            {},
        )

        assert results[0]["result"] == "ok"
        assert "error" in results[1]


class TestSyncAnalystAdapter:
    """Tests for SyncAnalystAdapter."""

    @pytest.mark.asyncio
    async def test_adapter_calls_sync_run(self):
        """Test that adapter calls the sync analyst's run method."""
        sync_agent = MagicMock()
        sync_agent.run = MagicMock(return_value={"result": "sync result"})

        adapter = SyncAnalystAdapter(sync_agent)
        result = await adapter.arun({})

        assert result["result"] == "sync result"
        sync_agent.run.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_adapter_passes_input_data(self):
        """Test that adapter passes input data to sync agent."""
        sync_agent = MagicMock()
        sync_agent.run = MagicMock(return_value={})

        adapter = SyncAnalystAdapter(sync_agent)
        await adapter.arun({"symbol": "BTC", "trade_date": "2026-04-01"})

        sync_agent.run.assert_called_once_with({
            "symbol": "BTC",
            "trade_date": "2026-04-01",
        })

    @pytest.mark.asyncio
    async def test_adapter_runs_in_thread(self):
        """Test that adapter runs sync code in a separate thread."""
        import threading

        sync_agent = MagicMock()
        captured_args = []

        def capture_args(input_data):
            captured_args.append(input_data)
            return {"result": "ok"}

        sync_agent.run = capture_args

        adapter = SyncAnalystAdapter(sync_agent)
        await adapter.arun({"test": "data"})

        assert len(captured_args) == 1
        assert captured_args[0] == {"test": "data"}
