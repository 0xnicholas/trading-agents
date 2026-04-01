"""
Default configuration for crypto trading agent.

This module provides the baseline configuration that can be overridden
by environment variables or user config files.
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class HyperliquidConfig:
    """Hyperliquid-specific settings."""
    # API
    mainnet_url: str = "https://api.hyperliquid.xyz"
    testnet_url: str = "https://api.hyperliquid-testnet.xyz"
    use_testnet: bool = False

    # Cache
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_dir: str = "/tmp/hl_cache"

    # Rate limiting
    requests_per_second: float = 5.0
    burst_size: int = 10


@dataclass
class LLMConfig:
    """LLM provider settings."""
    provider: Literal["openai", "anthropic", "azure"] = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 60

    # API keys (set via env vars)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


@dataclass
class TradingConfig:
    """Trading behavior settings."""
    # Default symbol
    default_symbol: str = "BTC"

    # Position limits
    max_position_size_pct: float = 1.0  # Max % of portfolio
    max_leverage: int = 20

    # Risk thresholds
    min_confidence_to_trade: float = 0.6
    max_funding_rate_pct: float = 0.5  # Max annualized funding %

    # Backtest mode
    backtest_mode: bool = False
    backtest_date: str | None = None  # YYYY-MM-DD


@dataclass
class AgentConfig:
    """Agent behavior settings."""
    # Output
    output_language: str = "English"

    # Analysis
    candle_intervals: list[str] = field(
        default_factory=lambda: ["1h", "4h", "1d"]
    )
    indicators_periods: dict[str, int] = field(
        default_factory=lambda: {
            "atr": 14,
            "rsi": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "boll_period": 20,
            "boll_std": 2,
        }
    )

    # Orderbook
    orderbook_depth: int = 20


@dataclass
class Config:
    """Root configuration container."""
    hyperliquid: HyperliquidConfig = field(default_factory=HyperliquidConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        import os

        config = cls()

        # Hyperliquid
        hl = config.hyperliquid
        hl.use_testnet = os.getenv("HL_USE_TESTNET", "0") == "1"
        if ttl := os.getenv("HL_CACHE_TTL"):
            hl.cache_ttl_seconds = int(ttl)
        if rps := os.getenv("HL_RPS"):
            hl.requests_per_second = float(rps)

        # LLM
        llm = config.llm
        llm.openai_api_key = os.getenv("OPENAI_API_KEY")
        llm.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if model := os.getenv("LLM_MODEL"):
            llm.model_name = model
        if temp := os.getenv("LLM_TEMPERATURE"):
            llm.temperature = float(temp)

        # Trading
        trading = config.trading
        if symbol := os.getenv("TRADING_SYMBOL"):
            trading.default_symbol = symbol
        trading.backtest_mode = os.getenv("BACKTEST_MODE", "0") == "1"
        if date := os.getenv("BACKTEST_DATE"):
            trading.backtest_date = date
        if min_conf := os.getenv("MIN_CONFIDENCE"):
            trading.min_confidence_to_trade = float(min_conf)

        # Agent
        agent = config.agent
        if lang := os.getenv("OUTPUT_LANGUAGE"):
            agent.output_language = lang

        return config


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global config singleton."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
