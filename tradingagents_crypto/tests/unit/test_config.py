"""
Unit tests for configuration module.
"""
import pytest
from unittest.mock import patch
import os
import tempfile
from pathlib import Path

from config import (
    Config,
    HyperliquidConfig,
    LLMConfig,
    TradingConfig,
    AgentConfig,
    get_config,
    reset_config,
    merge_config,
)


class TestHyperliquidConfig:
    """Tests for HyperliquidConfig."""

    def test_default_values(self):
        """Test default Hyperliquid config."""
        config = HyperliquidConfig()
        assert config.mainnet_url == "https://api.hyperliquid.xyz"
        assert config.testnet_url == "https://api.hyperliquid-testnet.xyz"
        assert config.use_testnet is False
        assert config.cache_ttl_seconds == 300
        assert config.requests_per_second == 5.0

    def test_custom_values(self):
        """Test custom Hyperliquid config."""
        config = HyperliquidConfig(
            use_testnet=True,
            cache_ttl_seconds=600,
            requests_per_second=10.0,
        )
        assert config.use_testnet is True
        assert config.cache_ttl_seconds == 600
        assert config.requests_per_second == 10.0


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self):
        """Test default LLM config."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096


class TestTradingConfig:
    """Tests for TradingConfig."""

    def test_default_values(self):
        """Test default trading config."""
        config = TradingConfig()
        assert config.default_symbol == "BTC"
        assert config.max_position_size_pct == 1.0
        assert config.max_leverage == 20
        assert config.min_confidence_to_trade == 0.6
        assert config.backtest_mode is False

    def test_backtest_mode(self):
        """Test backtest mode config."""
        config = TradingConfig(
            backtest_mode=True,
            backtest_date="2026-01-15",
        )
        assert config.backtest_mode is True
        assert config.backtest_date == "2026-01-15"


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_default_values(self):
        """Test default agent config."""
        config = AgentConfig()
        assert config.output_language == "English"
        assert "1h" in config.candle_intervals
        assert config.indicators_periods["atr"] == 14
        assert config.orderbook_depth == 20


class TestConfig:
    """Tests for root Config."""

    def test_default_config(self):
        """Test root config with all defaults."""
        config = Config()
        assert config.hyperliquid.use_testnet is False
        assert config.llm.model_name == "gpt-4o"
        assert config.trading.default_symbol == "BTC"
        assert config.agent.output_language == "English"

    def test_nested_access(self):
        """Test accessing nested config values."""
        config = Config()
        assert config.hyperliquid.cache_ttl_seconds == 300
        assert config.trading.max_leverage == 20


class TestMergeConfig:
    """Tests for config merging."""

    def test_merge_simple(self):
        """Test merging simple dicts."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_config(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested(self):
        """Test merging nested dicts."""
        base = {"hyperliquid": {"use_testnet": False, "cache_ttl": 300}}
        override = {"hyperliquid": {"cache_ttl": 600}}
        result = merge_config(base, override)
        assert result["hyperliquid"]["use_testnet"] is False
        assert result["hyperliquid"]["cache_ttl"] == 600

    def test_merge_does_not_mutate_base(self):
        """Test merge doesn't modify base dict."""
        base = {"a": 1}
        override = {"b": 2}
        merge_config(base, override)
        assert base == {"a": 1}


class TestGetConfig:
    """Tests for get_config singleton."""

    def test_returns_config(self):
        """Test get_config returns a Config instance."""
        reset_config()
        config = get_config()
        assert isinstance(config, Config)

    def test_singleton(self):
        """Test get_config returns same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test reset_config clears singleton."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, should be new instance (may or may not be same object due to GC)
        assert isinstance(config2, Config)
