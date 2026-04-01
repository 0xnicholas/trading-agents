"""
Unit tests for Phase 2 analysts.
"""
import pytest
from tradingagents_crypto.agents.analysts.ethereum_onchain_analyst import (
    EthereumOnChainReport,
    EthereumOnChainSignals,
    _create_report_from_data,
)
from tradingagents_crypto.agents.analysts.solana_dex_analyst import (
    SolanaDexReport,
    SolanaDexSignals,
    _create_report_from_data as sol_create_report,
)
from tradingagents_crypto.agents.analysts.cross_chain_macro_analyst import (
    CrossChainMacroReport,
    CrossChainSignals,
    _create_report_from_data as macro_create_report,
)


class TestEthereumOnChainReport:
    """Tests for EthereumOnChainReport schema."""

    def test_create_report(self):
        """Test creating ETH report."""
        eth_data = {
            "spot_price": {"price_usd": 3500.0, "change_24h_pct": 2.5, "confidence": 0.75},
            "funding": {"funding_rate": 0.0001, "annualized": 0.1095, "confidence": 0.85},
            "onchain": {
                "gas": {"label": "medium", "confidence": 0.6},
                "staking": {"ratio": 0.28, "label": "high", "confidence": 0.65},
                "defi_tvl": {"tvl_usd": 50_000_000_000, "label": "dominant", "confidence": 0.8},
                "active_addresses": {"proxy_addresses": 1_000_000, "confidence": 0.5},
            },
        }

        report = _create_report_from_data(eth_data, None)

        assert isinstance(report, EthereumOnChainReport)
        assert report.direction in ("bullish", "bearish", "neutral")
        assert 0 <= report.confidence <= 1.0
        assert len(report.summary) > 0
        assert len(report.narrative) > 0

    def test_bearish_high_funding(self):
        """Test high funding = bearish."""
        eth_data = {
            "spot_price": {"price_usd": 3500.0, "confidence": 0.75},
            "funding": {"funding_rate": 0.001, "annualized": 1.0, "confidence": 0.85},  # 0.1% = high
            "onchain": {
                "gas": {"label": "high", "confidence": 0.6},
                "staking": {"ratio": 0.3, "label": "high", "confidence": 0.65},
                "defi_tvl": {"tvl_usd": 50_000_000_000, "confidence": 0.8},
                "active_addresses": {"confidence": 0.5},
            },
        }

        report = _create_report_from_data(eth_data, None)

        assert report.direction == "bearish"


class TestSolanaDexReport:
    """Tests for SolanaDexReport schema."""

    def test_create_report(self):
        """Test creating SOL report."""
        sol_data = {
            "spot_price": {"price_usd": 150.0, "change_24h_pct": 5.2, "confidence": 0.8},
            "dex": {"total_tvl": 200_000_000, "confidence": 0.7},
            "meme": [],
        }

        report = sol_create_report(sol_data)

        assert isinstance(report, SolanaDexReport)
        assert report.direction in ("bullish", "bearish", "neutral")
        assert 0 <= report.confidence <= 1.0

    def test_bullish_momentum(self):
        """Test high positive change = bullish."""
        sol_data = {
            "spot_price": {"price_usd": 160.0, "change_24h_pct": 10.0, "confidence": 0.8},
            "dex": {"total_tvl": 200_000_000, "confidence": 0.7},
            "meme": [],
        }

        report = sol_create_report(sol_data)

        assert report.direction == "bullish"


class TestCrossChainMacroReport:
    """Tests for CrossChainMacroReport schema."""

    def test_create_report(self):
        """Test creating macro report."""
        macro_data = {
            "btc_dominance": {"btc_dominance": 52.0, "confidence": 0.75},
            "fear_greed": {"value": 35, "label": "Fear", "confidence": 0.5},
            "stablecoin_flow": {"change_24h_pct": 0.5, "verdict": "Mild inflow", "confidence": 0.5},
            "correlation": {"btc_eth_corr_7d": 0.85, "btc_sol_corr_7d": 0.72, "confidence": 0.7},
        }

        report = macro_create_report(macro_data)

        assert isinstance(report, CrossChainMacroReport)
        assert report.market_regime in ("risk_on", "risk_off", "neutral")
        assert 0 <= report.confidence <= 1.0

    def test_risk_off_regime(self):
        """Test fear + high BTC.D = risk_off."""
        macro_data = {
            "btc_dominance": {"btc_dominance": 55.0, "confidence": 0.75},
            "fear_greed": {"value": 25, "label": "Extreme Fear", "confidence": 0.5},
            "stablecoin_flow": {"change_24h_pct": -2.0, "verdict": "Outflow", "confidence": 0.5},
            "correlation": {"btc_eth_corr_7d": 0.8, "btc_sol_corr_7d": 0.7, "confidence": 0.7},
        }

        report = macro_create_report(macro_data)

        assert report.market_regime == "risk_off"

    def test_risk_on_regime(self):
        """Test greed + low BTC.D = risk_on."""
        macro_data = {
            "btc_dominance": {"btc_dominance": 42.0, "confidence": 0.75},
            "fear_greed": {"value": 75, "label": "Greed", "confidence": 0.5},
            "stablecoin_flow": {"change_24h_pct": 2.0, "verdict": "Inflow", "confidence": 0.5},
            "correlation": {"btc_eth_corr_7d": 0.8, "btc_sol_corr_7d": 0.7, "confidence": 0.7},
        }

        report = macro_create_report(macro_data)

        assert report.market_regime == "risk_on"
