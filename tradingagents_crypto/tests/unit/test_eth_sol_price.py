"""
Unit tests for ETH and SOL price modules.
"""
import pytest
from unittest.mock import MagicMock, patch

from tradingagents_crypto.dataflows.ethereum import price as eth_price


class TestCheckPriceDeviation:
    """Tests for check_price_deviation function."""

    def test_normal_deviation(self):
        """Test normal deviation (< 1%) passes."""
        result = eth_price.check_price_deviation(
            eth_price=3500.0,
            hl_mark_px=3510.0,
        )
        assert result["warning"] is False
        assert result["deviation_pct"] == pytest.approx(0.28, rel=0.1)
        assert result["confidence_adjustment"] == 0.0

    def test_high_deviation_warning(self):
        """Test high deviation (> 1%) triggers warning."""
        result = eth_price.check_price_deviation(
            eth_price=3500.0,
            hl_mark_px=3650.0,  # ~4% deviation
        )
        assert result["warning"] is True
        assert result["confidence_adjustment"] == -0.1

    def test_zero_price_handling(self):
        """Test zero price is handled."""
        result = eth_price.check_price_deviation(
            eth_price=0.0,
            hl_mark_px=3500.0,
        )
        assert result["warning"] is False
        assert result["deviation_pct"] == 0.0


class TestETHSolPrice:
    """Tests for ETH/SOL price integration."""

    def test_get_eth_price_structure(self):
        """Test ETH price returns correct structure."""
        with patch("tradingagents_crypto.dataflows.coincap.CoinCapClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.get_eth_price.return_value = {
                "price_usd": 3500.0,
                "change_24h_pct": 2.5,
                "market_cap": 420_000_000_000.0,
                "volume_24h": 15_000_000_000.0,
                "rank": 2,
                "confidence": 0.75,
            }

            result = eth_price.get_eth_price()

            assert "price_usd" in result
            assert "confidence" in result
            assert result["price_usd"] == 3500.0
