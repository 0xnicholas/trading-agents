"""
Exposure Monitor.

Monitors position exposure against portfolio limits.
"""
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

logger = logging.getLogger(__name__)

# Exposure limits
MAX_SINGLE_ASSET_EXPOSURE = 0.20   # 20% of total equity per asset
MAX_ONE_WAY_EXPOSURE = 0.60        # 60% of total equity for one-way exposure
MAX_LEVERAGE = 20                   # Maximum allowed leverage
MIN_DIVERSITY_ASSETS = 3            # Minimum number of different assets for diversification warning
MAX_TOTAL_EXPOSURE = 0.40           # 40% of total equity for total exposure limit


@dataclass
class Position:
    """A trading position."""
    symbol: str
    side: Literal["long", "short"]
    size_usd: float           # Position size in USD
    entry_price: float
    current_price: float
    leverage: float = 1.0     # Leverage of this specific position


@dataclass
class ExposureViolation:
    """Details of an exposure violation."""
    rule: str
    detail: str
    action: Literal["reject", "warn"]


@dataclass
class ExposureCheckResult:
    """Result of exposure check."""
    violations: list[ExposureViolation] = field(default_factory=list)
    warnings: list[ExposureViolation] = field(default_factory=list)
    approved: bool = True
    total_exposure_usd: float = 0.0
    exposure_by_symbol: dict = field(default_factory=dict)


def check_exposure(
    positions: list[Position],
    total_equity: float,
    new_position: Optional[Position] = None,
) -> ExposureCheckResult:
    """
    Check if positions comply with exposure limits.

    Rules:
    - Single asset limit: 20% of total equity
    - One-way exposure limit: 60% of total equity
    - Maximum leverage: 20x
    - Minimum diversity: >= 3 assets (warning)

    Args:
        positions: Current list of positions
        total_equity: Total portfolio equity in USD
        new_position: Optional new position to check

    Returns:
        ExposureCheckResult with violations, warnings, and approval status
    """
    violations = []
    warnings = []

    if total_equity <= 0:
        logger.warning("Total equity is zero or negative, rejecting all positions")
        return ExposureCheckResult(
            violations=[ExposureViolation("equity", "Total equity is zero or negative", "reject")],
            approved=False,
        )

    # Add new position to list for calculation
    all_positions = list(positions)
    if new_position:
        all_positions.append(new_position)

    if not all_positions:
        return ExposureCheckResult(approved=True)

    # Calculate exposure by symbol
    # For each symbol, calculate net exposure (long - short) and gross exposure
    symbol_exposure = {}

    for pos in all_positions:
        if pos.symbol not in symbol_exposure:
            symbol_exposure[pos.symbol] = {"long": 0.0, "short": 0.0, "gross": 0.0}

        if pos.side == "long":
            symbol_exposure[pos.symbol]["long"] += pos.size_usd
        else:
            symbol_exposure[pos.symbol]["short"] += pos.size_usd
        symbol_exposure[pos.symbol]["gross"] += pos.size_usd

    # Check single asset limit (uses net exposure for hedged positions)
    for symbol, exposure in symbol_exposure.items():
        net_exposure = abs(exposure["long"] - exposure["short"])
        exposure_pct = net_exposure / total_equity
        if exposure_pct > MAX_SINGLE_ASSET_EXPOSURE:
            violations.append(ExposureViolation(
                rule="单币种上限",
                detail=f"{symbol} 占比 {exposure_pct:.1%} > {MAX_SINGLE_ASSET_EXPOSURE:.1%}",
                action="reject",
            ))

    # Check one-way exposure (net long or net short per direction)
    total_long = sum(e["long"] for e in symbol_exposure.values())
    total_short = sum(e["short"] for e in symbol_exposure.values())

    long_pct = total_long / total_equity
    short_pct = total_short / total_equity

    if long_pct > MAX_ONE_WAY_EXPOSURE:
        violations.append(ExposureViolation(
            rule="单向暴露上限",
            detail=f"多仓占比 {long_pct:.1%} > {MAX_ONE_WAY_EXPOSURE:.1%}",
            action="reject",
        ))

    if short_pct > MAX_ONE_WAY_EXPOSURE:
        violations.append(ExposureViolation(
            rule="单向暴露上限",
            detail=f"空仓占比 {short_pct:.1%} > {MAX_ONE_WAY_EXPOSURE:.1%}",
            action="reject",
        ))

    # Check maximum leverage
    for pos in all_positions:
        if pos.leverage > MAX_LEVERAGE:
            violations.append(ExposureViolation(
                rule="最大杠杆",
                detail=f"{pos.symbol} 杠杆 {pos.leverage}x > {MAX_LEVERAGE}x",
                action="reject",
            ))

    # Check diversification (warning only)
    unique_symbols = len(symbol_exposure)
    if unique_symbols < MIN_DIVERSITY_ASSETS:
        warnings.append(ExposureViolation(
            rule="分散度不足",
            detail=f"仅 {unique_symbols} 个币种，建议至少 {MIN_DIVERSITY_ASSETS} 个",
            action="warn",
        ))

    # Calculate total exposure (net, so hedged positions don't over-count)
    total_long = sum(e["long"] for e in symbol_exposure.values())
    total_short = sum(e["short"] for e in symbol_exposure.values())
    total_exposure = sum(e["gross"] for e in symbol_exposure.values())
    net_exposure_pct = abs(total_long - total_short) / total_equity

    # Check total net exposure limit
    if net_exposure_pct > MAX_TOTAL_EXPOSURE:
        violations.append(ExposureViolation(
            rule="总暴露上限",
            detail=f"总暴露 {net_exposure_pct:.1%} > {MAX_TOTAL_EXPOSURE:.1%}",
            action="reject",
        ))

    # Determine if approved
    has_rejects = any(v.action == "reject" for v in violations)
    approved = not has_rejects

    return ExposureCheckResult(
        violations=violations,
        warnings=warnings,
        approved=approved,
        total_exposure_usd=total_exposure,
        exposure_by_symbol={
            symbol: {
                "long": exp["long"],
                "short": exp["short"],
                "net": exp["long"] - exp["short"],
                "gross": exp["gross"],
            }
            for symbol, exp in symbol_exposure.items()
        },
    )


def get_max_position_size(
    total_equity: float,
    current_exposure: float,
    max_exposure_pct: float = MAX_SINGLE_ASSET_EXPOSURE,
) -> float:
    """
    Calculate maximum position size allowed.

    Args:
        total_equity: Total portfolio equity
        current_exposure: Current exposure to this symbol
        max_exposure_pct: Maximum exposure percentage (default 20%)

    Returns:
        Maximum position size in USD
    """
    max_total = total_equity * max_exposure_pct
    available = max_total - current_exposure
    return max(0.0, available)
