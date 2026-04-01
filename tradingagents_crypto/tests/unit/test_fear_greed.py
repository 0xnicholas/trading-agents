"""
Unit tests for Fear & Greed client.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.macro.fear_greed import FearGreedClient


@pytest.fixture
def mock_cache():
    """Mock cache that always returns None."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


class TestFearGreedClient:
    """Tests for FearGreedClient."""

    def test_get_current_success(self, mock_cache):
        """Test getting current Fear & Greed."""
        mock_response = {
            "data": [{
                "value": "35",
                "value_classification": "Fear",
                "timestamp": "1712000000",
            }]
        }

        with patch("tradingagents_crypto.dataflows.macro.fear_greed.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = FearGreedClient(cache=mock_cache)
            result = client.get_current()

            assert result["value"] == 35
            assert result["label"] == "Fear"
            assert result["confidence"] == 0.5

    def test_get_current_empty_data(self, mock_cache):
        """Test handling empty data."""
        mock_response = {"data": []}

        with patch("tradingagents_crypto.dataflows.macro.fear_greed.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = FearGreedClient(cache=mock_cache)
            result = client.get_current()

            assert result["value"] == 50  # Default
            assert result["label"] == "Neutral"

    def test_get_label_from_value(self, mock_cache):
        """Test label mapping from value (Alternative.me standard)."""
        client = FearGreedClient(cache=mock_cache)

        # Alternative.me classification: 0-25=Extreme Fear, 25-50=Fear, 50-75=Greed, 75-100=Extreme Greed
        assert client.get_label_from_value(10) == "Extreme Fear"
        assert client.get_label_from_value(30) == "Fear"
        assert client.get_label_from_value(50) == "Fear"  # 50 is upper bound of Fear
        assert client.get_label_from_value(51) == "Greed"  # 51 starts Greed
        assert client.get_label_from_value(70) == "Greed"
        assert client.get_label_from_value(90) == "Extreme Greed"

    def test_interpret_buy_opportunity(self, mock_cache):
        """Test interpretation for extreme fear = buy opportunity."""
        mock_response = {
            "data": [{
                "value": "15",
                "value_classification": "Extreme Fear",
                "timestamp": "1712000000",
            }]
        }

        with patch("tradingagents_crypto.dataflows.macro.fear_greed.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = FearGreedClient(cache=mock_cache)
            result = client.interpret()

            assert result["signal"] == "buy_opportunity"
            assert "Extreme Fear" in result["reason"]

    def test_interpret_sell_opportunity(self, mock_cache):
        """Test interpretation for extreme greed = sell opportunity."""
        mock_response = {
            "data": [{
                "value": "85",
                "value_classification": "Extreme Greed",
                "timestamp": "1712000000",
            }]
        }

        with patch("tradingagents_crypto.dataflows.macro.fear_greed.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get.return_value.json.return_value = mock_response
            mock_session.get.return_value.raise_for_status = MagicMock()

            client = FearGreedClient(cache=mock_cache)
            result = client.interpret()

            assert result["signal"] == "sell_opportunity"

    def test_cached_result(self, mock_cache):
        """Test cached result is returned."""
        cached_data = {"value": 40, "label": "Fear", "confidence": 0.5}
        mock_cache.get.return_value = cached_data

        client = FearGreedClient(cache=mock_cache)
        result = client.get_current()

        assert result == cached_data
