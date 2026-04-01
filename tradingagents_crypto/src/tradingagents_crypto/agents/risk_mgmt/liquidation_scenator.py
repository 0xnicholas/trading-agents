"""
Liquidation Scenator.

Calculates liquidation prices and safety buffers for crypto perpetual positions.
"""
import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

# Safety thresholds
SAFE_THRESHOLD = 0.10   # > 10% → safe
CAUTION_THRESHOLD = 0.05  # 5-10% → caution
DANGER_THRESHOLD = 0.05   # < 5% → danger


@dataclass
class LiquidationResult:
    """Result of liquidation analysis."""
    liquidation_price: float
    distance_to_liq_pct: float   # Safety buffer as percentage
    recommendation: Literal["safe", "caution", "danger"]
    max_safe_leverage: float


def calc_liquidation(
    direction: Literal["long", "short"],
    entry_price: float,
    current_price: float,
    leverage: float,
    margin_mode: Literal["isolated", "cross"] = "isolated",
) -> LiquidationResult:
    """
    Calculate liquidation price and safety buffer.

    Isolated Margin:
        long: liq_price = entry_price * (1 - 1 / leverage)
        short: liq_price = entry_price * (1 + 1 / leverage)

    Cross Margin:
        Simplified: liq_price ≈ entry_price * (1 - 1 / (leverage * mm_ratio))
        where mm_ratio ≈ 0.005 (0.5% maintenance margin)

    Args:
        direction: Position direction (long or short)
        entry_price: Entry price of the position
        current_price: Current market price
        leverage: Leverage level (1-125)
        margin_mode: "isolated" or "cross" margin

    Returns:
        LiquidationResult with liquidation price, safety buffer, and recommendation
    """
    if leverage <= 0:
        raise ValueError("Leverage must be positive")
    if leverage == 1:
        # No leverage = no liquidation (entry = liq price for long)
        return LiquidationResult(
            liquidation_price=entry_price,
            distance_to_liq_pct=0.0,
            recommendation="danger",
            max_safe_leverage=1.0,
        )

    if margin_mode == "isolated":
        if direction == "long":
            liq_price = entry_price * (1 - 1 / leverage)
        else:
            liq_price = entry_price * (1 + 1 / leverage)
    else:
        # Cross margin simplified formula
        # Maintenance margin ratio ~0.5%
        mm_ratio = 0.005
        if direction == "long":
            liq_price = entry_price * (1 - 1 / (leverage * mm_ratio))
        else:
            liq_price = entry_price * (1 + 1 / (leverage * mm_ratio))

    # Calculate distance to liquidation
    if direction == "long":
        distance_pct = (current_price - liq_price) / current_price
    else:
        distance_pct = (liq_price - current_price) / current_price

    distance_pct = max(0.0, distance_pct)  # Cap at 0

    # Determine recommendation
    if distance_pct > SAFE_THRESHOLD:
        recommendation = "safe"
    elif distance_pct > CAUTION_THRESHOLD:
        recommendation = "caution"
    else:
        recommendation = "danger"

    # Calculate max safe leverage for current price
    # When at liquidation boundary (distance_pct=0), use leverage - 1
    # Otherwise use: max_safe_lev = 1 / (distance_pct + 1/leverage)
    # This gives ~leverage-1 when distance=0, scales down as distance grows.
    if distance_pct == 0:
        max_safe_lev = leverage - 1
    else:
        denominator = distance_pct + 1 / leverage
        max_safe_lev = 1 / denominator

    return LiquidationResult(
        liquidation_price=round(liq_price, 4),
        distance_to_liq_pct=round(distance_pct, 4),
        recommendation=recommendation,
        max_safe_leverage=round(min(max_safe_lev, 125), 2),  # Max HL leverage is 125x
    )


def get_position_risk(
    direction: Literal["long", "short"],
    entry_price: float,
    current_price: float,
    leverage: float,
    margin_mode: Literal["isolated", "cross"] = "isolated",
) -> dict:
    """
    Get a dictionary representation of position risk.

    Args:
        direction: Position direction
        entry_price: Entry price
        current_price: Current market price
        leverage: Leverage level
        margin_mode: Margin mode

    Returns:
        Dictionary with risk information
    """
    result = calc_liquidation(direction, entry_price, current_price, leverage, margin_mode)
    return {
        "liquidation_price": result.liquidation_price,
        "distance_to_liq_pct": result.distance_to_liq_pct,
        "recommendation": result.recommendation,
        "max_safe_leverage": result.max_safe_leverage,
    }
