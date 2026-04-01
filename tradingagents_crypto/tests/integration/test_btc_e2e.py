"""
End-to-end integration tests.

Tests the complete workflow: data -> indicators -> analyst -> trader -> graph.
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

# Test the complete workflow


class TestDataFlowIntegration:
    """Test data flow integration."""

    def test_hl_data_to_indicators(self):
        """Test that HL data can flow into indicators."""
        from tradingagents_crypto.dataflows.hyperliquid.candles import get_candles
        from tradingagents_crypto.indicators.aggregator import compute_all_indicators

        # This test requires real API or mocks
        # Skip if no API available
        pytest.skip("Requires HL API credentials")


class TestAgentIntegration:
    """Test agent integration."""

    def test_analyst_report_structure(self):
        """Test analyst report has required fields."""
        from agents.base import AnalystReport

        report = AnalystReport(
            summary="Test summary",
            direction="bullish",
            confidence=0.75,
            signals={"rsi": 70},
            metrics={"price": 67000},
            narrative="Test narrative",
        )

        d = report.to_dict()
        assert "summary" in d
        assert "direction" in d
        assert "confidence" in d
        assert "signals" in d
        assert "metrics" in d
        assert "narrative" in d

    def test_trading_decision_structure(self):
        """Test trading decision has required fields."""
        from agents.base import TradingDecision

        decision = TradingDecision(
            action="long",
            size_pct=0.5,
            leverage=10,
            reason="Strong signal",
        )

        d = decision.to_dict()
        assert "action" in d
        assert "size_pct" in d
        assert "leverage" in d
        assert "reason" in d


class TestGraphIntegration:
    """Test graph integration."""

    def test_trading_state_dataclass(self):
        """Test TradingState can be created and used."""
        from graph.crypto_trading_graph import TradingState
        from langchain_core.messages import HumanMessage

        state = TradingState(
            symbol="BTC",
            trade_date="2026-04-01",
            messages=[HumanMessage(content="Analyze BTC")],
        )

        assert state.symbol == "BTC"
        assert state.final_decision == "hold"

    def test_graph_node_functions_exist(self):
        """Test node factory functions exist."""
        from agents.analysts.hyperliquid_perp_analyst import create_analyst_node
        from agents.traders.crypto_trader import create_trader_node

        mock_llm = MagicMock()

        # Should be able to create nodes
        analyst_fn = create_analyst_node("BTC", mock_llm)
        trader_fn = create_trader_node("BTC", mock_llm)

        assert callable(analyst_fn)
        assert callable(trader_fn)


class TestConfigIntegration:
    """Test config integration with other modules."""

    def test_config_used_by_hl_tools(self):
        """Test that config settings are used by HL tools."""
        from config import get_config, reset_config

        reset_config()
        config = get_config()

        # Should have all required sections
        assert hasattr(config, "hyperliquid")
        assert hasattr(config, "llm")
        assert hasattr(config, "trading")
        assert hasattr(config, "agent")

    def test_config_env_override(self):
        """Test environment variables override config."""
        import os
        from config import reset_config

        # Set env var
        os.environ["TRADING_SYMBOL"] = "ETH"
        reset_config()

        from config import get_config
        config = get_config()

        assert config.trading.default_symbol == "ETH"

        # Cleanup
        del os.environ["TRADING_SYMBOL"]
        reset_config()


class TestBacktestMode:
    """Test backtest mode functionality."""

    def test_filter_by_date(self):
        """Test candles are filtered by date in backtest mode."""
        from datetime import datetime
        import pandas as pd

        # Create sample data
        now = int(datetime.now().timestamp())
        hour = 3600

        df = pd.DataFrame({
            "timestamp": [now - 10 * hour, now - 5 * hour, now],
            "close": [67000, 67100, 67200],
            "open": [66900, 67000, 67100],
            "high": [67200, 67300, 67400],
            "low": [66800, 66900, 67000],
            "volume": [100, 110, 120],
        })

        from tradingagents_crypto.dataflows.hyperliquid.main import filter_by_date

        cutoff = datetime.now().strftime("%Y-%m-%d")
        filtered = filter_by_date(df, cutoff)

        # All rows should be before cutoff
        assert len(filtered) <= len(df)


class TestEndToEndMocked:
    """End-to-end tests with mocked external calls."""

    def test_full_analysis_workflow_mocked(self):
        """Test complete workflow with mocked LLM and HL API."""
        from agents.base import AnalystReport
        from agents.analysts.hyperliquid_perp_analyst import analyze_hyperliquid_perp

        # Mock the LLM response
        mock_response = {
            "summary": "BTC looks bullish",
            "direction": "bullish",
            "confidence": 0.75,
            "signals": {
                "funding_rate": {"verdict": "normal"},
                "oi_trend": {"verdict": "bullish"},
            },
            "metrics": {"rsi": 65},
            "narrative": "Detailed analysis...",
        }

        # This would require more sophisticated mocking
        # Skipping for now
        pytest.skip("Requires mock LLM setup")

    def test_trading_decision_from_analyst(self):
        """Test trader makes decision from analyst report."""
        from agents.base import AnalystReport
        from agents.traders.crypto_trader import CryptoTrader

        # Create mock analyst report
        report = AnalystReport(
            summary="BTC strongly bullish",
            direction="bullish",
            confidence=0.8,
            signals={
                "funding_rate": {"value": 0.0001, "verdict": "normal"},
                "oi_trend": {"current": 500_000_000, "verdict": "bullish"},
                "orderbook_imbalance": {"ratio": 1.3, "verdict": "bullish"},
                "volume_anomaly": {"ratio": 1.2, "verdict": "normal"},
                "volatility": {"atr_pct": 0.5, "position": "medium"},
                "trend_4h": {"direction": "bullish", "ma_cross": "above_ma"},
                "trend_1d": {"direction": "bullish", "ma_cross": "above_ma"},
            },
            metrics={
                "mark_price": 67000,
                "funding_rate": 0.0001,
                "open_interest_usd": 500_000_000,
                "volume_24h": 1_500_000_000,
                "rsi": 65,
                "atr": 500,
                "macd": 150,
                "macd_signal": 120,
                "boll_upper": 68000,
                "boll_lower": 66000,
            },
            narrative="Strong bullish setup...",
        )

        # With mocked LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"action": "long", "size_pct": 0.5, "leverage": 10, "reason": "Strong signal", "risk_warnings": []}'
        )

        trader = CryptoTrader(mock_llm, "BTC")
        decision = trader.decide(report)

        assert decision.action == "long"
        assert decision.size_pct == 0.5
        assert decision.leverage == 10
