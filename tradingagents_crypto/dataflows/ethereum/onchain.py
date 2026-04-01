"""
Ethereum on-chain data.

Data sources:
- CoinCap: Gas price proxy, ETH staking
- DeFiLlama: TVL
"""
import logging

from tradingagents_crypto.dataflows.coincap import CoinCapClient

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_gas_price(cache=None) -> dict:
    """
    Get Gas price proxy from CoinCap.

    Note: CoinCap doesn't have direct Gas price,
    we use volume/activity as a proxy for on-chain activity.

    Returns:
        Dict with:
        - proxy_activity: float (volume-based activity score)
        - label: str ("high", "medium", "low")
        - confidence: float (0.6, approximation)
    """
    client = CoinCapClient(cache=cache)
    eth = client.get_asset("ethereum")

    if not eth:
        return {
            "proxy_activity": 0.0,
            "label": "unknown",
            "confidence": 0.3,
        }

    # Use 24h volume as proxy for on-chain activity
    volume = float(eth.get("volumeUsd24Hr", 0))
    price = float(eth.get("priceUsd", 1))

    # Normalize: higher volume = more activity
    if price > 0:
        # Activity score: volume / price gives approximate transaction count proxy
        activity_proxy = volume / price / 1_000_000  # Scale to millions
    else:
        activity_proxy = 0.0

    # Classify
    if activity_proxy > 5_000_000:  # > 5M ETH volume
        label = "high"
    elif activity_proxy > 1_000_000:  # > 1M ETH volume
        label = "medium"
    else:
        label = "low"

    return {
        "proxy_activity": round(activity_proxy, 2),
        "label": label,
        "confidence": 0.6,  # Approximation only
    }


def get_staking_ratio(cache=None) -> dict:
    """
    Get ETH staking ratio proxy.

    Note: This is an approximation. CoinCap doesn't expose
    direct staking data. We use supply-based proxy.

    Returns:
        Dict with:
        - ratio: float (0.0 - 1.0)
        - label: str
        - confidence: float (0.65)
    """
    client = CoinCapClient(cache=cache)
    ratio = client.get_eth_staking_ratio()

    # Classify
    if ratio > 0.9:
        label = "very_high"
    elif ratio > 0.7:
        label = "high"
    elif ratio > 0.5:
        label = "medium"
    elif ratio > 0.3:
        label = "low"
    else:
        label = "very_low"

    return {
        "ratio": round(ratio, 4),
        "label": label,
        "confidence": 0.65,  # Approximation
    }


def get_defi_tvl() -> dict:
    """
    Get ETH DeFi TVL.

    Note: DeFiLlama API was not tested due to VM network restrictions.
    This returns a placeholder - implement when API is accessible.

    Returns:
        Dict with placeholder values
    """
    # TODO: Implement DeFiLlama API call
    return {
        "tvl_eth": 0.0,
        "tvl_usd": 0.0,
        "label": "unknown",
        "status": "unavailable",
        "confidence": 0.3,
        "note": "DeFiLlama API not accessible from VM",
    }


def get_active_addresses(cache=None) -> dict:
    """
    Get active addresses proxy.

    Note: CoinCap doesn't expose active addresses.
    This is a placeholder using volume as proxy.

    Returns:
        Dict with proxy metric
    """
    client = CoinCapClient(cache=cache)
    eth = client.get_asset("ethereum")

    if not eth:
        return {
            "proxy_addresses": 0,
            "confidence": 0.3,
        }

    # Very rough proxy: volume / avg tx value
    volume = float(eth.get("volumeUsd24Hr", 0))
    price = float(eth.get("priceUsd", 1))

    # Assume avg tx ~ $100
    avg_tx = 100
    if price > 0:
        proxy = volume / avg_tx
    else:
        proxy = 0

    return {
        "proxy_addresses": int(proxy),
        "confidence": 0.5,  # Very rough approximation
    }
