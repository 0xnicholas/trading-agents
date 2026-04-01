"""
Liquidity Checker.

Estimates slippage based on position size and order book depth.
"""
import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)

# Slippage thresholds (in bps)
SLIPPAGE_LOW_THRESHOLD = 5      # < 5 bps → low risk
SLIPPAGE_MEDIUM_THRESHOLD = 20  # 5-20 bps → medium risk
SLIPPAGE_HIGH_THRESHOLD = 20    # > 20 bps → high risk

# Slippage model parameters
SLIPPAGE_POWER = 0.7   # Non-linear exponent: ratio^0.7
SLIPPAGE_SCALE = 10     # Scale factor
SLIPPAGE_MAX_BPS = 50   # Maximum slippage cap (50 bps)


@dataclass
class LiquidityCheckResult:
    """Result of liquidity check."""
    estimated_slippage_bps: float
    liquidity_risk: Literal["low", "medium", "high"]
    recommendation: Literal["正常开仓", "降低仓位", "拒绝"]
    depth_used: float   # The depth value used for calculation


def estimate_slippage(
    position_size_usd: float,
    bid_depth_usd: float,
    ask_depth_usd: float,
    side: Literal["long", "short"],
) -> float:
    """
    Estimate slippage in basis points (bps).

    Uses a non-linear model based on position size vs order book depth.

    Formula:
        depth = bid_depth if long else ask_depth
        ratio = position_size_usd / depth
        slippage_bps = min(ratio^0.7 * 10, 50)

    Args:
        position_size_usd: Size of the position in USD
        bid_depth_usd: Total bid depth on the order book
        ask_depth_usd: Total ask depth on the order book
        side: "long" (uses bid) or "short" (uses ask)

    Returns:
        Estimated slippage in basis points (bps)
    """
    if position_size_usd <= 0:
        return 0.0

    # Determine which depth to use
    if side == "long":
        depth = bid_depth_usd
    else:
        depth = ask_depth_usd

    # Handle zero depth
    if depth <= 0:
        logger.warning(f"Zero depth for {side}, returning max slippage")
        return SLIPPAGE_MAX_BPS

    # Calculate ratio
    ratio = position_size_usd / depth

    # Non-linear slippage model
    # slippage = min(ratio^power * scale, max)
    slippage_bps = min(ratio ** SLIPPAGE_POWER * SLIPPAGE_SCALE, SLIPPAGE_MAX_BPS)

    return round(slippage_bps, 2)


def check_liquidity(
    position_size_usd: float,
    bid_depth_usd: float,
    ask_depth_usd: float,
    side: Literal["long", "short"],
) -> LiquidityCheckResult:
    """
    Check liquidity and return recommendation.

    Args:
        position_size_usd: Position size in USD
        bid_depth_usd: Bid depth
        ask_depth_usd: Ask depth
        side: Position side

    Returns:
        LiquidityCheckResult with slippage estimate and recommendation
    """
    depth = bid_depth_usd if side == "long" else ask_depth_usd

    slippage_bps = estimate_slippage(position_size_usd, bid_depth_usd, ask_depth_usd, side)

    # Determine risk level
    if slippage_bps < SLIPPAGE_LOW_THRESHOLD:
        liquidity_risk = "low"
        recommendation = "正常开仓"
    elif slippage_bps < SLIPPAGE_MEDIUM_THRESHOLD:
        liquidity_risk = "medium"
        recommendation = "降低仓位"
    else:
        liquidity_risk = "high"
        recommendation = "拒绝"

    return LiquidityCheckResult(
        estimated_slippage_bps=slippage_bps,
        liquidity_risk=liquidity_risk,
        recommendation=recommendation,
        depth_used=depth,
    )


def get_required_depth_for_slippage(
    position_size_usd: float,
    target_slippage_bps: float,
    side: Literal["long", "short"],
) -> float:
    """
    Calculate required order book depth to achieve target slippage.

    Args:
        position_size_usd: Position size in USD
        target_slippage_bps: Target slippage in bps
        side: Position side

    Returns:
        Required depth in USD
    """
    # Inverse of slippage formula:
    # slippage = min(ratio^0.7 * 10, 50)
    # ratio = (slippage / 10) ^ (1/0.7)
    # depth = position_size / ratio

    effective_slippage = min(target_slippage_bps, SLIPPAGE_MAX_BPS)

    if effective_slippage <= 0:
        return 0.0

    ratio = (effective_slippage / SLIPPAGE_SCALE) ** (1 / SLIPPAGE_POWER)
    required_depth = position_size_usd / ratio

    return required_depth
