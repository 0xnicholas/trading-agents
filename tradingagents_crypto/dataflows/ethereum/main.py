"""
Ethereum data layer - unified entry point.

Aggregates all ETH-related data:
- Spot price (CoinCap)
- Funding rate (Bybit)
- On-chain metrics
"""
import logging
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _safe_get(
    func: Callable[[], T],
    field_name: str,
    default: Any,
) -> T:
    """
    Safely call a function and return default on failure.

    Args:
        func: Function to call
        field_name: Name for logging
        default: Default value on failure

    Returns:
        Result of func() or default
    """
    try:
        return func()
    except Exception as e:
        logger.warning(f"Failed to get {field_name}: {e}")
        return default


def get_eth_data(
    symbol: str = "ETH",
    use_cache: bool = True,
) -> dict:
    """
    Get comprehensive ETH data from all sources.

    Args:
        symbol: Currently only "ETH" supported
        use_cache: Whether to use cache (default True)

    Returns:
        Dict with:
        - symbol: str
        - spot_price: dict from CoinCap
        - funding: dict from Bybit
        - onchain: dict with gas, staking, tvl, addresses
        - timestamp: datetime
    """
    cache = CacheManager() if use_cache else None

    # Import here to avoid circular imports
    from . import price as eth_price
    from . import funding as eth_funding
    from . import onchain as eth_onchain

    result = {
        "symbol": symbol,
        "timestamp": datetime.now(timezone.utc),
    }

    # Get spot price
    result["spot_price"] = _safe_get(
        lambda: eth_price.get_eth_price(cache=cache),
        "ETH spot price",
        {"price_usd": 0.0, "confidence": 0.0},
    )

    # Get funding rate
    result["funding"] = _safe_get(
        lambda: eth_funding.get_eth_funding_rate(cache=cache),
        "ETH funding rate",
        {"funding_rate": 0.0, "confidence": 0.0},
    )

    # Get on-chain data
    gas = _safe_get(
        lambda: eth_onchain.get_gas_price(cache=cache),
        "Gas data",
        {"proxy_activity": 0.0, "label": "unknown", "confidence": 0.0},
    )
    staking = _safe_get(
        lambda: eth_onchain.get_staking_ratio(cache=cache),
        "Staking data",
        {"ratio": 0.0, "label": "unknown", "confidence": 0.0},
    )
    addresses = _safe_get(
        lambda: eth_onchain.get_active_addresses(cache=cache),
        "Active addresses",
        {"proxy_addresses": 0, "confidence": 0.0},
    )
    tvl = _safe_get(
        eth_onchain.get_defi_tvl,
        "TVL data",
        {"tvl_usd": 0.0, "status": "unavailable", "confidence": 0.0},
    )

    result["onchain"] = {
        "gas": gas,
        "staking": staking,
        "active_addresses": addresses,
        "defi_tvl": tvl,
    }

    return result
