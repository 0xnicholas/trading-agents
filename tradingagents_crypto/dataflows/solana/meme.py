"""
Solana Meme coin data.

Data source: GeckoTerminal API
"""
import logging

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 minutes


def get_meme_coins(
    limit: int = 10,
    cache=None,
) -> list[dict]:
    """
    Get top meme coins on Solana by liquidity.

    Note: GeckoTerminal API not tested due to VM network restrictions.
    This returns a placeholder - implement when API is accessible.

    Args:
        limit: Number of top coins to return

    Returns:
        List of dicts with:
        - symbol: str
        - name: str
        - price_usd: float
        - change_24h_pct: float
        - tvl_usd: float
        - volume_24h: float
        - confidence: float
    """
    # TODO: Implement GeckoTerminal API call when network is available
    return []


def get_meme_coin(symbol: str) -> dict:
    """
    Get data for a specific meme coin.

    Note: Placeholder - implement when API is accessible.
    """
    return {
        "symbol": symbol,
        "name": "",
        "price_usd": 0.0,
        "change_24h_pct": 0.0,
        "tvl_usd": 0.0,
        "volume_24h": 0.0,
        "confidence": 0.3,
        "note": "Not implemented - API not accessible",
    }


def calc_meme_turnover(
    volume_24h: float,
    tvl: float,
) -> dict:
    """
    Calculate meme coin turnover ratio.

    Args:
        volume_24h: 24h trading volume in USD
        tvl: Total value locked in USD

    Returns:
        Dict with:
        - ratio: float (volume / TVL)
        - label: str
        - confidence: float
    """
    if tvl <= 0:
        return {
            "ratio": 0.0,
            "label": "unknown",
            "confidence": 0.3,
        }

    ratio = volume_24h / tvl

    if ratio > 2.0:
        label = "extreme_speculation"
    elif ratio > 1.0:
        label = "high_speculation"
    elif ratio > 0.5:
        label = "moderate"
    else:
        label = "low_activity"

    return {
        "ratio": round(ratio, 2),
        "label": label,
        "confidence": 0.8,
    }
