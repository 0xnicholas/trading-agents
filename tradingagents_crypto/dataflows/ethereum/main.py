"""
Ethereum data layer - unified entry point.

Aggregates all ETH-related data:
- Spot price (CoinCap)
- Funding rate (Bybit)
- On-chain metrics
"""
import logging
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.hyperliquid.cache import CacheManager

logger = logging.getLogger(__name__)


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
    try:
        result["spot_price"] = eth_price.get_eth_price(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get ETH spot price: {e}")
        result["spot_price"] = {"price_usd": 0.0, "confidence": 0.0}

    # Get funding rate
    try:
        result["funding"] = eth_funding.get_eth_funding_rate(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get ETH funding rate: {e}")
        result["funding"] = {"funding_rate": 0.0, "confidence": 0.0}

    # Get on-chain data
    try:
        gas = eth_onchain.get_gas_price(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get Gas data: {e}")
        gas = {"proxy_activity": 0.0, "label": "unknown", "confidence": 0.0}

    try:
        staking = eth_onchain.get_staking_ratio(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get staking data: {e}")
        staking = {"ratio": 0.0, "label": "unknown", "confidence": 0.0}

    try:
        addresses = eth_onchain.get_active_addresses(cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get active addresses: {e}")
        addresses = {"proxy_addresses": 0, "confidence": 0.0}

    try:
        tvl = eth_onchain.get_defi_tvl()
    except Exception as e:
        logger.warning(f"Failed to get TVL data: {e}")
        tvl = {"tvl_usd": 0.0, "confidence": 0.0}

    result["onchain"] = {
        "gas": gas,
        "staking": staking,
        "active_addresses": addresses,
        "defi_tvl": tvl,
    }

    return result
