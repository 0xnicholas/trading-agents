"""
Integration tests for Phase 2 multi-chain features.
"""
import pytest
from unittest.mock import Mock, patch

from tradingagents_crypto.dataflows.macro.fear_greed import (
    FearGreedClient,
    get_fear_greed_index,
)
from tradingagents_crypto.dataflows.ethereum.gas import (
    EtherscanClient,
    get_gas_prices,
)
from tradingagents_crypto.graph.multi_chain_router import (
    MultiChainRouter,
    MultiChainState,
    create_multi_chain_graph,
)


class TestFearGreedIndex:
    """Test Fear & Greed Index data flow."""

    def test_get_fear_greed_index_success(self):
        """Test successful Fear & Greed Index fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "value": "65",
                    "value_classification": "Greed",
                    "timestamp": "1704067200",
                    "time_until_update": "3600",
                }
            ]
        }

        with patch('requests.Session.get', return_value=mock_response):
            result = get_fear_greed_index()

        assert result['value'] == 65
        assert result['classification'] == 'Greed'
        assert result['confidence'] == 0.9
        assert result['trend'] in ['improving', 'worsening', 'stable']

    def test_get_fear_greed_index_failure(self):
        """Test Fear & Greed Index failure handling."""
        with patch('requests.Session.get', side_effect=Exception("API Error")):
            result = get_fear_greed_index()

        assert result['value'] == 50
        assert result['classification'] == 'unknown'
        assert result['confidence'] == 0.3
        assert 'error' in result


class TestEtherscanGas:
    """Test Etherscan Gas Tracker."""

    def test_get_gas_prices_success(self):
        """Test successful gas price fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "1",
            "result": {
                "SafeGasPrice": "25",
                "ProposeGasPrice": "30",
                "FastGasPrice": "35",
                "suggestBaseFee": "28",
                "gasUsedRatio": "0.5,0.6,0.7,0.8",
            }
        }

        with patch('requests.Session.get', return_value=mock_response):
            result = get_gas_prices(api_key="test_key")

        assert result['safe'] == 25.0
        assert result['standard'] == 30.0
        assert result['fast'] == 35.0
        assert result['base_fee'] == 28.0
        assert result['classification'] in ['low', 'medium', 'high', 'extreme']
        assert result['confidence'] == 0.9

    def test_get_gas_prices_no_api_key(self):
        """Test gas price fetch without API key."""
        with patch.dict('os.environ', {}, clear=True):
            result = get_gas_prices()

        assert result['confidence'] == 0.3
        assert 'error' in result
        assert 'note' in result


class TestMultiChainRouter:
    """Test multi-chain routing logic."""

    def test_detect_chains_eth(self):
        """Test ETH chain detection."""
        chains = MultiChainRouter.detect_chains("Analyze Ethereum price")
        assert "eth" in chains

    def test_detect_chains_sol(self):
        """Test SOL chain detection."""
        chains = MultiChainRouter.detect_chains("Check Solana DEX liquidity")
        assert "sol" in chains

    def test_detect_chains_btc(self):
        """Test BTC chain detection."""
        chains = MultiChainRouter.detect_chains("Bitcoin dominance analysis")
        assert "btc" in chains

    def test_detect_chains_default(self):
        """Test default chain when none specified."""
        chains = MultiChainRouter.detect_chains("General market analysis")
        assert "btc" in chains

    def test_detect_analysis_type_funding(self):
        """Test funding rate analysis detection."""
        analysis_type = MultiChainRouter.detect_analysis_type("Check ETH funding rates")
        assert analysis_type == "funding"

    def test_detect_analysis_type_dex(self):
        """Test DEX analysis detection."""
        analysis_type = MultiChainRouter.detect_analysis_type("Solana DEX liquidity")
        assert analysis_type == "dex"

    def test_route_eth_funding(self):
        """Test routing for ETH funding analysis."""
        state = MultiChainState(user_request="ETH funding rate analysis")
        result = MultiChainRouter.route(state)

        assert "eth" in result.chains_needed
        assert result.analysis_type == "funding"
        assert any(t["type"] == "eth_funding" for t in result.tasks)
        assert any(t["type"] == "macro_analysis" for t in result.tasks)

    def test_route_multi_chain(self):
        """Test routing for multi-chain request."""
        state = MultiChainState(user_request="Compare ETH and SOL prices")
        result = MultiChainRouter.route(state)

        assert "eth" in result.chains_needed
        assert "sol" in result.chains_needed
        assert len(result.tasks) >= 3  # eth, sol, macro


class TestMultiChainGraph:
    """Test multi-chain graph compilation."""

    def test_create_graph(self):
        """Test graph creation."""
        graph = create_multi_chain_graph()
        assert graph is not None

    @pytest.mark.asyncio
    async def test_graph_execution(self):
        """Test graph execution with mock."""
        graph = create_multi_chain_graph()

        # Mock the analyst coordinator
        with patch('tradingagents_crypto.graph.multi_chain_router.analyst_coordinator') as mock_coord:
            mock_coord.return_value = {
                "analyst_results": {"test": "result"},
                "status": "completed",
            }

            # This would need actual async execution
            # For now, just verify graph structure
            assert graph is not None
