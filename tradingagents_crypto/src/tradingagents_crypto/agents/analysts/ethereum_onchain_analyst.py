"""
Ethereum OnChain Analyst.

Analyzes Ethereum on-chain data and produces trading signals.
"""
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from tradingagents_crypto.agents.base import AnalystReport
from tradingagents_crypto.agents.schema import (
    HyperliquidPerpReport,
    FundingSignal,
    OITrend,
    OrderbookImbalance,
    VolumeAnomaly,
    VolatilitySignal,
    TrendSignal,
)
from pydantic import BaseModel, Field
from typing import Literal

logger = logging.getLogger(__name__)


class EthereumOnChainSignals(BaseModel):
    """Signals from ETH on-chain analysis."""
    gas_sentiment: dict = Field(description="Gas activity signal")
    active_address_trend: dict = Field(description="Active address trend signal")
    staking_ratio: dict = Field(description="ETH staking ratio signal")
    tvl_rank: dict = Field(description="DeFi TVL dominance signal")
    funding_diff: dict = Field(description="Binance vs Hyperliquid funding diff")


class EthereumOnChainReport(BaseModel):
    """Ethereum on-chain analyst report."""
    summary: str = Field(max_length=200)
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    signals: EthereumOnChainSignals
    narrative: str


# System prompt for ETH analyst
ETH_ANALYST_PROMPT = """You are an expert analyst specializing in Ethereum on-chain data.

Analyze ETH market using:
- Spot price from CoinCap
- ETH-PERP funding rates (Binance/Bybit vs Hyperliquid)
- On-chain metrics: Gas activity, Staking ratio, DeFi TVL

## Your Task
Provide a clear bullish/bearish/neutral assessment with confidence.

## Output Format
Return a JSON object with:
{
  "summary": "1-2 sentence summary",
  "direction": "bullish | bearish | neutral",
  "confidence": 0.0-1.0,
  "signals": {
    "gas_sentiment": {"value": "high|medium|low", "confidence": 0.0-1.0},
    "active_address_trend": {"value": "rising|falling|stable", "confidence": 0.0-1.0},
    "staking_ratio": {"value": float, "label": "high|medium|low", "confidence": 0.0-1.0},
    "tvl_rank": {"value": float, "label": "dominant|significant|low", "confidence": 0.0-1.0},
    "funding_diff": {"value": float, "note": "Binance minus HL funding"}
  },
  "narrative": "Detailed paragraph"
}
"""


def analyze_ethereum_onchain(
    eth_data: dict,
    hl_funding: dict | None = None,
) -> EthereumOnChainReport:
    """
    Analyze ETH on-chain data.

    Args:
        eth_data: Data from get_eth_data()
        hl_funding: Optional Hyperliquid funding data for comparison

    Returns:
        EthereumOnChainReport
    """
    # Extract data
    spot = eth_data.get("spot_price", {})
    funding = eth_data.get("funding", {})
    onchain = eth_data.get("onchain", {})
    gas = onchain.get("gas", {})
    staking = onchain.get("staking", {})
    tvl = onchain.get("defi_tvl", {})
    addresses = onchain.get("active_addresses", {})

    # Build analysis prompt
    prompt = f"""
Analyze ETH market based on the following data:

=== ETH Spot Price ===
Price: ${spot.get('price_usd', 0):,.2f}
24h Change: {spot.get('change_24h_pct', 0):.2f}%
Confidence: {spot.get('confidence', 0):.2f}

=== ETH Funding Rate (Bybit) ===
8h Rate: {funding.get('funding_rate', 0):.6f}
Annualized: {funding.get('annualized', 0):.2%}
Confidence: {funding.get('confidence', 0):.2f}

=== On-Chain Metrics ===
Gas Activity: {gas.get('label', 'unknown')} (proxy)
Staking Ratio: {staking.get('label', 'unknown')} ({staking.get('ratio', 0):.2%})
TVL Status: {tvl.get('label', 'unknown')}
Active Addresses Proxy: {addresses.get('proxy_addresses', 0):,}

=== Hyperliquid Funding (for comparison) ===
{f"8h Rate: {hl_funding.get('funding_rate', 0):.6f}" if hl_funding else "N/A"}

Provide your analysis as JSON.
"""

    messages = [
        SystemMessage(content=ETH_ANALYST_PROMPT),
        HumanMessage(content=prompt),
    ]

    # Return a structured report
    # In real implementation, this would call an LLM
    # For now, create a placeholder report based on data
    return _create_report_from_data(eth_data, hl_funding)


def _create_report_from_data(
    eth_data: dict,
    hl_funding: dict | None,
) -> EthereumOnChainReport:
    """Create report from data without LLM call (for testing)."""
    spot = eth_data.get("spot_price", {})
    funding = eth_data.get("funding", {})
    onchain = eth_data.get("onchain", {})
    gas = onchain.get("gas", {})
    staking = onchain.get("staking", {})
    tvl = onchain.get("defi_tvl", {})
    addresses = onchain.get("active_addresses", {})

    # Determine direction from funding
    funding_rate = funding.get("funding_rate", 0)
    if funding_rate > 0.0003:  # > 0.03%
        direction = "bearish"  # High funding = bears receive
    elif funding_rate < -0.0003:
        direction = "bullish"  # Negative funding = bulls receive
    else:
        direction = "neutral"

    # Confidence weighted average
    confidences = [
        spot.get("confidence", 0),
        funding.get("confidence", 0),
        gas.get("confidence", 0),
        staking.get("confidence", 0),
    ]
    avg_confidence = sum(c for c in confidences if c > 0) / max(len([c for c in confidences if c > 0]), 1)

    # Funding diff
    funding_diff_value = 0.0
    if hl_funding:
        funding_diff_value = funding_rate - hl_funding.get("funding_rate", 0)

    return EthereumOnChainReport(
        summary=f"ETH {'bullish' if direction == 'bullish' else 'neutral' if direction == 'neutral' else 'bearish'} based on funding and on-chain metrics",
        direction=direction,
        confidence=avg_confidence,
        signals=EthereumOnChainSignals(
            gas_sentiment={
                "value": gas.get("label", "unknown"),
                "confidence": gas.get("confidence", 0.5),
            },
            active_address_trend={
                "value": "stable",  # TODO: implement with history
                "confidence": addresses.get("confidence", 0.5),
            },
            staking_ratio={
                "value": staking.get("ratio", 0),
                "label": staking.get("label", "unknown"),
                "confidence": staking.get("confidence", 0.5),
            },
            tvl_rank={
                "value": tvl.get("tvl_usd", 0),
                "label": tvl.get("label", "unknown"),
                "confidence": tvl.get("confidence", 0.5),
            },
            funding_diff={
                "value": funding_diff_value,
                "note": f"Bybit-HL: {funding_diff_value:.6f}",
                "confidence": min(funding.get("confidence", 0.5), 0.85),
            },
        ),
        narrative=f"ETH funding rate is {funding_rate:.4f} (annualized {funding.get('annualized', 0):.2%}). "
                  f"Gas activity is {gas.get('label', 'unknown')}. "
                  f"Staking ratio is {staking.get('label', 'unknown')} at {staking.get('ratio', 0):.1%}.",
    )
