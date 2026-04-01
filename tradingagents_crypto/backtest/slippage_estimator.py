"""
Slippage Estimator.

Estimates execution slippage based on position size and order book depth.
"""
import logging
from typing import Literal

logger = logging.getLogger(__name__)

# Model parameters
SLIPPAGE_POWER = 0.7   # Non-linear exponent: ratio^0.7
SLIPPAGE_SCALE = 5     # Scale factor (reduced so simple slippage stays < 1%)
SLIPPAGE_MAX_BPS = 50   # Maximum slippage cap (50 bps)


def estimate_slippage(
    position_size_usd: float,
    bid_depth_usd: float,
    ask_depth_usd: float,
    side: Literal["long", "short"],
) -> float:
    """
    Estimate slippage in basis points (bps).

    Non-linear model:
        depth = bid_depth if long else ask_depth
        ratio = position_size_usd / depth
        slippage_bps = min(ratio^0.7 * 10, 50)

    Note: This is an estimation model, not historical data.

    Args:
        position_size_usd: Size of the position in USD
        bid_depth_usd: Total bid depth on order book
        ask_depth_usd: Total ask depth on order book
        side: "long" (uses bid) or "short" (uses ask)

    Returns:
        Estimated slippage in bps
    """
    if position_size_usd <= 0:
        return 0.0

    # Select appropriate depth
    depth = bid_depth_usd if side == "long" else ask_depth_usd

    # Handle edge case
    if depth <= 0:
        logger.warning(f"Zero depth for {side}, returning max slippage")
        return SLIPPAGE_MAX_BPS

    # Calculate ratio
    ratio = position_size_usd / depth

    # Non-linear slippage estimation
    slippage_bps = min(ratio ** SLIPPAGE_POWER * SLIPPAGE_SCALE, SLIPPAGE_MAX_BPS)

    return round(slippage_bps, 2)


def estimate_slippage_simple(
    position_size_usd: float,
    depth_usd: float,
) -> float:
    """
    Simple slippage estimate using average depth.

    Args:
        position_size_usd: Position size in USD
        depth_usd: Average order book depth

    Returns:
        Slippage in bps
    """
    if depth_usd <= 0:
        return SLIPPAGE_MAX_BPS

    ratio = position_size_usd / depth_usd
    return min(ratio ** SLIPPAGE_POWER * SLIPPAGE_SCALE, SLIPPAGE_MAX_BPS)


def depth_required_for_target_slippage(
    position_size_usd: float,
    target_slippage_bps: float,
) -> float:
    """
    Calculate required order book depth for target slippage.

    Args:
        position_size_usd: Position size in USD
        target_slippage_bps: Target slippage in bps

    Returns:
        Required depth in USD
    """
    effective_slippage = min(target_slippage_bps, SLIPPAGE_MAX_BPS)

    if effective_slippage <= 0:
        return 0.0

    # Inverse of slippage formula: ratio = (slippage / 10) ^ (1/0.7)
    ratio = (effective_slippage / SLIPPAGE_SCALE) ** (1 / SLIPPAGE_POWER)
    required_depth = position_size_usd / ratio

    return required_depth


def calculate_execution_price(
    mid_price: float,
    slippage_bps: float,
    side: Literal["long", "short"],
) -> float:
    """
    Calculate execution price including slippage.

    Args:
        mid_price: Mid price of asset
        slippage_bps: Slippage in bps
        side: "long" (slippage increases price) or "short" (slippage decreases price)

    Returns:
        Execution price after slippage
    """
    slippage_multiplier = 1 + (slippage_bps / 10000)

    if side == "long":
        return mid_price * slippage_multiplier
    else:
        return mid_price / slippage_multiplier
