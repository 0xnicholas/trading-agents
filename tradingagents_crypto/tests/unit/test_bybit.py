"""
Unit tests for Bybit API client.
"""
import pytest
from unittest.mock import MagicMock, patch

from tradingagents_crypto.dataflows.bybit import BybitClient


@pytest.fixture
def mock_cache():
    """Mock cache that always returns None."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


class TestBybitClient:
    """Tests for BybitClient."""

    def test_get_funding_rate_success(self, mock_cache):
        """Test getting funding rate successfully."""
        mock_response = {
            "result": {
                "list": [{
                    "symbol": "ETHUSDT",
                    "fundingRate": "0.00010000",
                    "nextFundingTime": "1712000000000",
                }]
            }
        }

        with patch("tradingagents_crypto.dataflows.bybit.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = BybitClient(cache=mock_cache)
            result = client.get_funding_rate("ETHUSDT")

            assert result["symbol"] == "ETHUSDT"
            assert result["funding_rate"] == 0.0001
            assert result["annualized"] == pytest.approx(0.1095, rel=0.01)
            assert result["confidence"] == 0.85

    def test_get_funding_rate_empty_result(self, mock_cache):
        """Test handling empty result."""
        mock_response = {"result": {"list": []}}

        with patch("tradingagents_crypto.dataflows.bybit.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = BybitClient(cache=mock_cache)
            result = client.get_funding_rate("ETHUSDT")

            assert result["funding_rate"] == 0.0
            assert result["confidence"] == 0.5  # Lower on failure

    def test_get_eth_funding_convenience(self, mock_cache):
        """Test get_eth_funding is an alias."""
        mock_response = {
            "result": {
                "list": [{
                    "symbol": "ETHUSDT",
                    "fundingRate": "0.00015000",
                    "nextFundingTime": "1712000000000",
                }]
            }
        }

        with patch("tradingagents_crypto.dataflows.bybit.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = BybitClient(cache=mock_cache)
            result = client.get_eth_funding()

            assert result["symbol"] == "ETHUSDT"
            assert result["funding_rate"] == 0.00015

    def test_cached_result(self, mock_cache):
        """Test cached result is returned."""
        cached_data = {
            "symbol": "ETHUSDT",
            "funding_rate": 0.0001,
            "annualized": 0.1095,
            "confidence": 0.85,
        }
        mock_cache.get.return_value = cached_data

        client = BybitClient(cache=mock_cache)
        result = client.get_funding_rate("ETHUSDT")

        assert result == cached_data
