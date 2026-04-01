"""
Unit tests for CoinCap API client.
"""
import pytest
from unittest.mock import MagicMock, patch

from tradingagents_crypto.dataflows.coincap import CoinCapClient


@pytest.fixture
def mock_cache():
    """Mock cache that always returns None (cache miss)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


@pytest.fixture
def mock_session():
    """Mock requests session."""
    with patch("tradingagents_crypto.dataflows.coincap.requests.Session") as mock:
        yield mock.return_value


class TestCoinCapClient:
    """Tests for CoinCapClient."""

    def test_get_asset_success(self, mock_cache, mock_session):
        """Test getting asset data successfully."""
        mock_session.get.return_value.json.return_value = {
            "data": {
                "id": "ethereum",
                "symbol": "ETH",
                "priceUsd": "3500.00",
                "changePercent24Hr": "2.5",
                "marketCapUsd": "420000000000",
                "volumeUsd24Hr": "15000000000",
                "rank": "2",
            }
        }
        mock_session.get.return_value.raise_for_status = MagicMock()

        client = CoinCapClient(cache=mock_cache)
        result = client.get_asset("ethereum")

        assert result["id"] == "ethereum"
        assert float(result["priceUsd"]) == 3500.0
        assert float(result["changePercent24Hr"]) == 2.5

    def test_get_asset_cached(self, mock_cache):
        """Test cache hit returns cached data."""
        cached_data = {"id": "ethereum", "priceUsd": "3500.00"}
        mock_cache.get.return_value = cached_data

        client = CoinCapClient(cache=mock_cache)
        result = client.get_asset("ethereum")

        assert result == cached_data

    def test_get_eth_price_structure(self, mock_cache, mock_session):
        """Test ETH price returns correct structure."""
        mock_session.get.return_value.json.return_value = {
            "data": {
                "id": "ethereum",
                "priceUsd": "3500.00",
                "changePercent24Hr": "2.5",
                "marketCapUsd": "420000000000",
                "volumeUsd24Hr": "15000000000",
                "rank": "2",
            }
        }
        mock_session.get.return_value.raise_for_status = MagicMock()

        client = CoinCapClient(cache=mock_cache)
        result = client.get_eth_price()

        assert "price_usd" in result
        assert "change_24h_pct" in result
        assert "confidence" in result
        assert result["confidence"] == 0.75

    def test_get_sol_price_structure(self, mock_cache, mock_session):
        """Test SOL price returns correct structure."""
        mock_session.get.return_value.json.return_value = {
            "data": {
                "id": "solana",
                "priceUsd": "150.00",
                "changePercent24Hr": "5.0",
                "marketCapUsd": "65000000000",
                "volumeUsd24Hr": "3000000000",
                "rank": "5",
            }
        }
        mock_session.get.return_value.raise_for_status = MagicMock()

        client = CoinCapClient(cache=mock_cache)
        result = client.get_sol_price()

        assert "price_usd" in result
        assert result["price_usd"] == 150.0
        assert result["confidence"] == 0.8

    def test_get_btc_dominance_calculation(self, mock_cache, mock_session):
        """Test BTC dominance is calculated correctly."""
        mock_session.get.return_value.json.return_value = {
            "data": [
                {"id": "bitcoin", "marketCapUsd": "1000000000000"},
                {"id": "ethereum", "marketCapUsd": "400000000000"},
                {"id": "tether", "marketCapUsd": "100000000000"},
            ]
        }
        mock_session.get.return_value.raise_for_status = MagicMock()

        client = CoinCapClient(cache=mock_cache)
        dominance = client.get_btc_dominance()

        # BTC cap = 1T, total = 1.5T, dominance = 66.67%
        assert dominance == pytest.approx(66.67, rel=0.1)

    def test_get_stablecoin_supplies_structure(self, mock_cache, mock_session):
        """Test stablecoin supplies returns correct structure."""
        mock_session.get.return_value.json.side_effect = iter([
            {"data": {"id": "tether", "supply": "100000000000", "changePercent24Hr": "0.01"}},
            {"data": {"id": "usd-coin", "supply": "50000000000", "changePercent24Hr": "0.02"}},
        ])
        mock_session.get.return_value.raise_for_status = MagicMock()

        client = CoinCapClient(cache=mock_cache)
        result = client.get_stablecoin_supplies()

        assert "tether_supply" in result
        assert "usd_coin_supply" in result
        assert "total_supply" in result
        assert result["total_supply"] == 150_000_000_000
        assert result["confidence"] == 0.5
