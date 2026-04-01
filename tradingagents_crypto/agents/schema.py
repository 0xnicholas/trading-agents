"""
Pydantic schemas for agent outputs.

Defines the expected structure for LLM outputs.
"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class FundingSignal(BaseModel):
    """Funding rate signal."""
    value: float
    annualized: float
    direction: Literal["positive (longs pay)", "negative (shorts pay)"]
    verdict: Literal["normal", "elevated", "extreme"]


class OITrend(BaseModel):
    """Open interest trend signal."""
    current: float
    change_24h_pct: float
    direction: Literal["expanding", "contracting", "neutral"]
    verdict: Literal["bullish", "bearish", "neutral"]


class OrderbookImbalance(BaseModel):
    """Orderbook imbalance signal."""
    bid_depth: float
    ask_depth: float
    imbalance_ratio: float
    verdict: Literal["bullish", "bearish", "neutral"]


class VolumeAnomaly(BaseModel):
    """Volume anomaly signal."""
    volume_24h: float
    volume_ma7: float
    ratio: float
    verdict: Literal["normal", "elevated", "anomalous"]


class VolatilitySignal(BaseModel):
    """Volatility signal."""
    atr_24h: float
    atr_pct: float
    position: Literal["low", "medium", "high", "extreme"]


class TrendSignal(BaseModel):
    """Trend direction signal."""
    direction: Literal["bullish", "bearish", "neutral"]
    ma_cross: Literal["above_ma", "below_ma"]


class HyperliquidPerpSignals(BaseModel):
    """All signals from Hyperliquid Perp Analyst."""
    funding_rate: FundingSignal
    oi_trend: OITrend
    orderbook_imbalance: OrderbookImbalance
    volume_anomaly: VolumeAnomaly
    volatility: VolatilitySignal
    trend_4h: TrendSignal
    trend_1d: TrendSignal


class HyperliquidPerpMetrics(BaseModel):
    """Numeric metrics from analysis."""
    mark_price: float
    index_price: float
    funding_rate: float
    open_interest_usd: float
    volume_24h: float
    rsi: float = Field(ge=0, le=100)
    atr: float
    macd: float
    macd_signal: float
    boll_upper: float
    boll_lower: float


class HyperliquidPerpReport(BaseModel):
    """
    Complete analyst report for Hyperliquid Perpetuals.

    This is the output schema for HyperliquidPerpAnalyst.
    """
    summary: str = Field(max_length=200)
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    signals: HyperliquidPerpSignals
    metrics: HyperliquidPerpMetrics
    narrative: str = Field(min_length=100)

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("bullish", "bearish", "neutral"):
            raise ValueError(f"Invalid direction: {v}")
        return v


class TradeSignal(BaseModel):
    """Trade decision signal."""
    action: Literal["long", "short", "close", "hold"]
    size_pct: float = Field(ge=0.0, le=1.0)
    leverage: int = Field(ge=1, le=20)
    entry_reason: str
    risk_adjusted: bool


class RiskReport(BaseModel):
    """Risk evaluation report."""
    approved: bool
    warnings: list[str] = Field(default_factory=list)
    adjustments: dict[str, float] = Field(default_factory=dict)
    recommendation: Literal["safe", "caution", "danger"]


class FinalDecision(BaseModel):
    """Final trading decision."""
    action: Literal["long", "short", "close", "hold"]
    size_pct: float
    leverage: int
    reason: str
    risk_checks: RiskReport
