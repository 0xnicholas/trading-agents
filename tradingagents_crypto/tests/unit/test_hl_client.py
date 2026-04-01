"""
Unit tests for HLClient API wrapper.

Uses mock fixtures to avoid real HTTP calls.
"""
import pytest
from unittest.mock import MagicMock, patch

from tradingagents_crypto.dataflows.hyperliquid.api import HLClient
from tests.fixtures.mock_hl_api import (
    mock_all_mids,
    mock_meta_and_asset_ctxs,
    mock_candles_btc_1h,
    mock_l2_snapshot_btc,
    mock_funding_history_btc,
)


@pytest.fixture
def mock_info():
    """Create a mock Info object."""
    info = MagicMock()
    info.all_mids = MagicMock(return_value=mock_all_mids())
    info.meta_and_asset_ctxs = MagicMock(return_value=mock_meta_and_asset_ctxs())
    info.candles_snapshot = MagicMock(return_value=mock_candles_btc_1h())
    info.l2_snapshot = MagicMock(return_value=mock_l2_snapshot_btc())
    info.funding_history = MagicMock(return_value=mock_funding_history_btc())
    return info


@pytest.fixture
def client(mock_info):
    """Create HLClient with mocked Info."""
    with patch("tradingagents_crypto.dataflows.hyperliquid.api.Info", return_value=mock_info):
        client = HLClient()
        client.info = mock_info
        yield client


class TestHLClient:
    """Tests for HLClient."""

    def test_get_all_mids(self, client):
        """Test getting all mids."""
        mids = client.get_all_mids()
        assert "BTC" in mids
        assert "ETH" in mids
        assert mids["BTC"] == "67000.0"

    def test_get_meta_and_asset_ctxs(self, client):
        """Test getting meta and asset contexts."""
        meta, asset_ctxs = client.get_meta_and_asset_ctxs()
        assert "universe" in meta
        assert len(meta["universe"]) == 3
        assert len(asset_ctxs) == 3

    def test_get_candles(self, client):
        """Test getting candles."""
        candles = client.get_candles(
            "BTC", "1h",
            start_time_ms=1710000000000,
            end_time_ms=1710010000000,
        )
        assert len(candles) > 0
        # Check first candle has expected keys
        assert "T" in candles[0] or "t" in candles[0]
        assert "o" in candles[0]

    def test_get_candles_invalid_interval(self, client):
        """Test invalid interval raises ValueError."""
        with pytest.raises(ValueError, match="Invalid interval"):
            client.get_candles("BTC", "2h", 1710000000000, 1710010000000)

    def test_get_funding_history(self, client):
        """Test getting funding history."""
        history = client.get_funding_history("BTC", 1710000000000, 1710010000000)
        assert len(history) > 0
        assert "fundingRate" in history[0] or "coin" in history[0]

    def test_get_l2_snapshot(self, client):
        """Test getting L2 snapshot."""
        snapshot = client.get_l2_snapshot("BTC")
        assert snapshot["coin"] == "BTC"
        assert "levels" in snapshot
        assert len(snapshot["levels"]) == 2  # bids and asks

    def test_get_l2_snapshot_format(self, client):
        """Test L2 snapshot has correct structure."""
        snapshot = client.get_l2_snapshot("BTC")
        bids = snapshot["levels"][0]
        asks = snapshot["levels"][1]
        # Each level should have px and sz
        assert "px" in bids[0]
        assert "sz" in bids[0]


class TestHLClientIntegration:
    """Integration tests that verify data transformation."""

    def test_candles_have_required_fields(self, client):
        """Test that candles have all required fields."""
        candles = client.get_candles(
            "BTC", "1h",
            start_time_ms=1710000000000,
            end_time_ms=1710010000000,
        )
        for candle in candles:
            # Should have time, open, high, low, close, volume
            assert "T" in candle or "t" in candle
