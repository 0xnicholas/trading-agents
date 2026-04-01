"""
Cross-Chain Macro Analyst.

Analyzes BTC dominance, Fear & Greed, Stablecoin flows, and cross-chain correlations.
"""
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from pydantic import BaseModel, Field
from typing import Literal

logger = logging.getLogger(__name__)


class CrossChainSignals(BaseModel):
    """Signals from cross-chain macro analysis."""
    btc_dominance: dict = Field(description="BTC dominance signal")
    fear_greed: dict = Field(description="Fear & Greed index signal")
    stablecoin_flow: dict = Field(description="Stablecoin flow signal")
    correlation: dict = Field(description="Cross-chain correlation signal")


class CrossChainMacroReport(BaseModel):
    """Cross-chain macro analyst report."""
    summary: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    market_regime: Literal["risk_on", "risk_off", "neutral"]
    signals: CrossChainSignals
    narrative: str


MACRO_ANALYST_PROMPT = """You are an expert macro analyst specializing in cross-chain market regime detection.

Analyze the overall market using:
- BTC Dominance (rising = risk_off, falling = altcoin season)
- Fear & Greed Index (extreme fear = buy opportunity, extreme greed = sell)
- Stablecoin flows (inflow = bullish, outflow = bearish)
- Cross-chain correlations (high correlation = systematic moves)

## Market Regime Detection
- risk_on: Risk assets rising together, BTC.D falling, Greed
- risk_off: Risk assets falling, BTC.D rising, Fear
- neutral: Mixed signals

## Output Format
Return JSON:
{
  "summary": "1-2 sentence summary",
  "confidence": 0.0-1.0,
  "market_regime": "risk_on | risk_off | neutral",
  "signals": {
    "btc_dominance": {"value": float, "trend": "rising|falling|stable", "verdict": "string", "confidence": 0.0-1.0},
    "fear_greed": {"value": int, "label": "Fear|Greed|Neutral", "confidence": 0.0-1.0},
    "stablecoin_flow": {"value": float, "verdict": "string", "confidence": 0.0-1.0},
    "correlation": {"btc_eth": float, "btc_sol": float, "verdict": "string", "confidence": 0.0-1.0}
  },
  "narrative": "Detailed paragraph"
}
"""


def analyze_cross_chain_macro(
    macro_data: dict,
) -> CrossChainMacroReport:
    """
    Analyze cross-chain macro data.

    Args:
        macro_data: Data from get_macro_data()

    Returns:
        CrossChainMacroReport
    """
    btc_dom = macro_data.get("btc_dominance", {})
    fear_greed = macro_data.get("fear_greed", {})
    stablecoin = macro_data.get("stablecoin_flow", {})
    correlation = macro_data.get("correlation", {})

    return _create_report_from_data(macro_data)


def _create_report_from_data(macro_data: dict) -> CrossChainMacroReport:
    """Create report from data without LLM call."""
    btc_dom = macro_data.get("btc_dominance", {})
    fear_greed = macro_data.get("fear_greed", {})
    stablecoin = macro_data.get("stablecoin_flow", {})
    correlation = macro_data.get("correlation", {})

    # Determine regime
    fg_value = fear_greed.get("value", 50)
    btc_dom_val = btc_dom.get("btc_dominance", 50)
    stable_change = stablecoin.get("change_24h_pct", 0)

    # Regime logic
    if fg_value <= 30 and btc_dom_val > 50:
        regime = "risk_off"
    elif fg_value >= 70 and btc_dom_val < 45:
        regime = "risk_on"
    elif stable_change > 1 and btc_dom_val < 50:
        regime = "risk_on"
    elif stable_change < -1:
        regime = "risk_off"
    else:
        regime = "neutral"

    # Confidence
    confidences = [
        btc_dom.get("confidence", 0),
        fear_greed.get("confidence", 0),
        stablecoin.get("confidence", 0),
        correlation.get("confidence", 0),
    ]
    avg_conf = sum(c for c in confidences if c > 0) / max(len([c for c in confidences if c > 0]), 1)

    # Summary
    regime_desc = {
        "risk_on": "risk-on mode - market is risk-friendly",
        "risk_off": "risk-off mode - market is risk-averse",
        "neutral": "neutral mode - mixed signals",
    }

    return CrossChainMacroReport(
        summary=f"Market in {regime_desc.get(regime, 'neutral')}.",
        confidence=avg_conf,
        market_regime=regime,
        signals=CrossChainSignals(
            btc_dominance={
                "value": btc_dom_val,
                "trend": "rising" if btc_dom_val > 52 else "falling" if btc_dom_val < 48 else "stable",
                "verdict": f"BTC.D at {btc_dom_val:.1f}%",
                "confidence": btc_dom.get("confidence", 0.5),
            },
            fear_greed={
                "value": fg_value,
                "label": fear_greed.get("label", "Neutral"),
                "confidence": fear_greed.get("confidence", 0.5),
            },
            stablecoin_flow={
                "value": stablecoin.get("change_24h_pct", 0),
                "verdict": stablecoin.get("verdict", "Unknown"),
                "confidence": stablecoin.get("confidence", 0.5),
            },
            correlation={
                "btc_eth": correlation.get("btc_eth_corr_7d", 0),
                "btc_sol": correlation.get("btc_sol_corr_7d", 0),
                "verdict": correlation.get("verdict", "Unknown"),
                "confidence": correlation.get("confidence", 0.5),
            },
        ),
        narrative=f"BTC dominance is {btc_dom_val:.1f}%. "
                  f"Fear & Greed is at {fg_value} ({fear_greed.get('label', 'Unknown')}). "
                  f"Stablecoin flow is {stable_change:+.2f}%. "
                  f"Market regime: {regime}.",
    )
