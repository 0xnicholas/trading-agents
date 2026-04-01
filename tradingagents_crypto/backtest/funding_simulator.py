"""
Funding Rate Simulator.

Calculates funding rate PnL for perpetual futures positions.
"""
import logging
from typing import Literal

logger = logging.getLogger(__name__)


def calc_funding_pnl(
    position_side: Literal["long", "short"],
    position_value: float,
    funding_rate: float,
) -> float:
    """
    Calculate funding fee PnL for a position.

    Funding rules:
    - funding_rate > 0 (positive): Longs pay shorts
        - long: pnl = -funding_rate * position_value (you pay)
        - short: pnl = funding_rate * position_value (you receive)
    - funding_rate < 0 (negative): Shorts pay longs
        - long: pnl = -funding_rate * position_value = positive (you receive)
        - short: pnl = funding_rate * position_value = negative (you pay)

    Args:
        position_side: "long" or "short"
        position_value: Notional value of position in USD
        funding_rate: Funding rate (e.g., 0.0001 for 0.01%)

    Returns:
        Funding PnL (positive = profit, negative = loss)
    """
    if position_side == "long":
        # Longs pay when rate is positive
        pnl = -funding_rate * position_value
    else:
        # Shorts receive when rate is positive
        pnl = funding_rate * position_value

    return pnl


def calc_funding_cost(
    position_side: Literal["long", "short"],
    position_value: float,
    funding_rate: float,
    hours: float,
) -> float:
    """
    Calculate total funding cost over a period.

    Args:
        position_side: "long" or "short"
        position_value: Notional value in USD
        funding_rate: Funding rate (per 8h period)
        hours: Duration in hours

    Returns:
        Total funding cost (positive = you pay, negative = you receive)
    """
    # Funding settles every 8 hours
    periods = hours / 8.0
    per_period_cost = calc_funding_pnl(position_side, position_value, funding_rate)

    return per_period_cost * periods


def annualize_funding_rate(rate: float) -> float:
    """
    Annualize a funding rate.

    Assumes 3 funding periods per day (every 8 hours).

    Args:
        rate: Funding rate (e.g., 0.0001 for 0.01% per 8h)

    Returns:
        Annualized rate as decimal
    """
    periods_per_day = 3
    periods_per_year = periods_per_day * 365

    return rate * periods_per_year


def format_funding_rate(rate: float) -> str:
    """
    Format funding rate as percentage string.

    Args:
        rate: Funding rate as decimal (e.g., 0.0001)

    Returns:
        Formatted string (e.g., "0.010% (annualized: 10.95%)")
    """
    rate_pct = rate * 100
    annualized = annualize_funding_rate(rate) * 100
    return f"{rate_pct:.4f}% (annualized: {annualized:.2f}%)"
