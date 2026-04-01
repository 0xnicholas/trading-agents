"""Risk management modules."""

from tradingagents_crypto.agents.risk_mgmt.liquidation_scenator import (
    calc_liquidation,
    get_position_risk,
    LiquidationResult,
)
from tradingagents_crypto.agents.risk_mgmt.hv_analyst import (
    analyze_hv,
    calculate_hv_from_returns,
    calculate_atr,
    HVAnalysis,
)
from tradingagents_crypto.agents.risk_mgmt.exposure_monitor import (
    check_exposure,
    get_max_position_size,
    Position,
    ExposureCheckResult,
    ExposureViolation,
)
from tradingagents_crypto.agents.risk_mgmt.liquidity_checker import (
    estimate_slippage,
    check_liquidity,
    get_required_depth_for_slippage,
    LiquidityCheckResult,
)

__all__ = [
    # Liquidation
    "calc_liquidation",
    "get_position_risk",
    "LiquidationResult",
    # HV Analyst
    "analyze_hv",
    "calculate_hv_from_returns",
    "calculate_atr",
    "HVAnalysis",
    # Exposure Monitor
    "check_exposure",
    "get_max_position_size",
    "Position",
    "ExposureCheckResult",
    "ExposureViolation",
    # Liquidity Checker
    "estimate_slippage",
    "check_liquidity",
    "get_required_depth_for_slippage",
    "LiquidityCheckResult",
]
