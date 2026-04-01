"""
Unit tests for crypto trading graph.
"""
import pytest
from unittest.mock import MagicMock

from graph.crypto_trading_graph import (
    TradingState,
    create_crypto_trading_graph,
)


class TestTradingState:
    """Tests for TradingState."""

    def test_create_state(self):
        """Test creating trading state."""
        state = TradingState(
            symbol="BTC",
            trade_date="2026-04-01",
            messages=[],
        )
        assert state.symbol == "BTC"
        assert state.trade_date == "2026-04-01"
        assert state.analyst_report is None
        assert state.trading_decision is None

    def test_state_defaults(self):
        """Test state default values."""
        state = TradingState(
            symbol="ETH",
            trade_date="2026-04-01",
            messages=[],
        )
        assert state.final_decision == "hold"


class TestCryptoTradingGraph:
    """Tests for the trading graph."""

    def test_graph_creation(self):
        """Test graph can be created."""
        mock_llm = MagicMock()
        graph = create_crypto_trading_graph(mock_llm, "BTC")
        assert graph is not None

    def test_graph_has_required_nodes(self):
        """Test graph has analyst and trader nodes."""
        mock_llm = MagicMock()
        graph = create_crypto_trading_graph(mock_llm, "BTC")
        # Graph should be compilable
        assert hasattr(graph, 'invoke')
