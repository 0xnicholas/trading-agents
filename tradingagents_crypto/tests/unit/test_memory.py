"""
Unit tests for shared memory.
"""
import pytest
import asyncio
from tradingagents_crypto.memory.shared_state import SharedMemory, SharedState


class TestSharedMemory:
    """Tests for SharedMemory."""

    @pytest.fixture
    def memory(self):
        """Create a SharedMemory instance without Redis."""
        return SharedMemory(use_redis=False)

    @pytest.mark.asyncio
    async def test_write_and_read(self, memory):
        """Test basic write and read."""
        state = SharedState(
            symbol="BTC",
            trade_date="2026-04-01",
            trace_id="test123",
        )
        await memory.write("test123", state)

        result = await memory.read("test123")
        assert result is not None
        assert result.symbol == "BTC"
        assert result.trace_id == "test123"

    @pytest.mark.asyncio
    async def test_concurrent_write(self, memory):
        """Test concurrent writes don't corrupt data."""
        import asyncio

        async def write(i):
            state = SharedState(
                symbol=f"COIN{i}",
                trade_date="2026-04-01",
                trace_id=f"trace{i}",
            )
            await memory.write(f"trace{i}", state)

        await asyncio.gather(*[write(i) for i in range(10)])

        for i in range(10):
            state = await memory.read(f"trace{i}")
            assert state.symbol == f"COIN{i}"

    @pytest.mark.asyncio
    async def test_nonexistent_read(self, memory):
        """Test reading non-existent key returns None."""
        result = await memory.read("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_fields(self, memory):
        """Test updating specific fields."""
        state = SharedState(
            symbol="BTC",
            trade_date="2026-04-01",
            trace_id="update_test",
        )
        await memory.write("update_test", state)

        await memory.update("update_test", final_decision="long")

        updated = await memory.read("update_test")
        assert updated.final_decision == "long"

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self, memory):
        """Test updating non-existent key raises KeyError."""
        with pytest.raises(KeyError):
            await memory.update("nonexistent", final_decision="long")

    @pytest.mark.asyncio
    async def test_delete(self, memory):
        """Test deleting a state."""
        state = SharedState(
            symbol="BTC",
            trade_date="2026-04-01",
            trace_id="delete_test",
        )
        await memory.write("delete_test", state)

        await memory.delete("delete_test")
        result = await memory.read("delete_test")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, memory):
        """Test deleting non-existent key doesn't raise."""
        await memory.delete("nonexistent")  # Should not raise


class TestSharedState:
    """Tests for SharedState dataclass."""

    def test_creation_default_values(self):
        """Test SharedState with default values."""
        state = SharedState(symbol="BTC", trade_date="2026-04-01")
        assert state.symbol == "BTC"
        assert state.final_decision == "hold"
        assert state.messages == []

    def test_creation_with_signals(self):
        """Test SharedState with analysis signals."""
        state = SharedState(
            symbol="BTC",
            trade_date="2026-04-01",
            btc_signal={"direction": "bullish", "confidence": 0.8},
            eth_signal={"direction": "neutral", "confidence": 0.5},
        )
        assert state.btc_signal["direction"] == "bullish"
        assert state.eth_signal["confidence"] == 0.5


class TestSharedMemoryIntegration:
    """Integration tests for SharedMemory with concurrent access."""

    @pytest.fixture
    def mem(self):
        """Create a SharedMemory instance for integration tests."""
        return SharedMemory(use_redis=False)

    @pytest.mark.asyncio
    async def test_parallel_reads(self, mem):
        """Test parallel reads of same key."""
        state = SharedState(symbol="BTC", trade_date="2026-04-01", trace_id="parallel_read")
        await mem.write("parallel_read", state)

        results = await asyncio.gather(*[
            mem.read("parallel_read") for _ in range(10)
        ])

        assert all(r.symbol == "BTC" for r in results)

    @pytest.mark.asyncio
    async def test_write_prevents_race_condition(self, mem):
        """Test that concurrent writes to different keys work correctly."""
        async def write_trace(trace_id: str, symbol: str):
            state = SharedState(symbol=symbol, trade_date="2026-04-01", trace_id=trace_id)
            await mem.write(trace_id, state)
            return trace_id

        await asyncio.gather(*[
            write_trace(f"race_{i}", f"SYM{i}") for i in range(20)
        ])

        for i in range(20):
            state = await mem.read(f"race_{i}")
            assert state.symbol == f"SYM{i}"
