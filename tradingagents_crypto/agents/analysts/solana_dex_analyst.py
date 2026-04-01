"""
Solana DEX / Meme Analyst.

Analyzes Solana DEX data and meme coin activity.
"""
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from pydantic import BaseModel, Field
from typing import Literal

logger = logging.getLogger(__name__)


class SolanaDexSignals(BaseModel):
    """Signals from Solana DEX analysis."""
    meme_liquidity: dict = Field(description="Meme coin liquidity signal")
    meme_turnover: dict = Field(description="Meme coin turnover ratio signal")
    sol_momentum: dict = Field(description="SOL price momentum signal")
    dex_volume_rank: dict = Field(description="DEX volume rank signal")


class SolanaDexReport(BaseModel):
    """Solana DEX analyst report."""
    summary: str = Field(max_length=200)
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    signals: SolanaDexSignals
    narrative: str


SOLANA_ANALYST_PROMPT = """You are an expert analyst specializing in Solana DEX and meme coin activity.

Analyze SOL market using:
- SOL spot price from CoinCap
- DEX liquidity from Jupiter/GeckoTerminal
- Meme coin activity and turnover

## Your Task
Assess the speculative activity level and SOL momentum.

## Output Format
Return JSON:
{
  "summary": "1-2 sentence summary",
  "direction": "bullish | bearish | neutral",
  "confidence": 0.0-1.0,
  "signals": {
    "meme_liquidity": {"value": "high|medium|low", "confidence": 0.0-1.0},
    "meme_turnover": {"value": float, "label": "elevated_speculation|normal", "confidence": 0.0-1.0},
    "sol_momentum": {"value": float, "label": "bullish_24h|bearish_24h|neutral", "confidence": 0.0-1.0},
    "dex_volume_rank": {"value": int, "label": "top_dex|secondary", "confidence": 0.0-1.0}
  },
  "narrative": "Detailed paragraph"
}
"""


def analyze_solana_dex(
    sol_data: dict,
) -> SolanaDexReport:
    """
    Analyze Solana DEX data.

    Args:
        sol_data: Data from get_sol_data()

    Returns:
        SolanaDexReport
    """
    spot = sol_data.get("spot_price", {})
    dex = sol_data.get("dex", {})
    meme = sol_data.get("meme", [])

    # Build prompt
    prompt = f"""
Analyze SOL market based on:

=== SOL Price ===
Price: ${spot.get('price_usd', 0):,.2f}
24h Change: {spot.get('change_24h_pct', 0):.2f}%
Confidence: {spot.get('confidence', 0):.2f}

=== DEX Liquidity ===
Total TVL: ${dex.get('total_tvl', 0):,.0f}
Note: {dex.get('note', '')}

=== Meme Coin Activity ===
Top coins tracked: {len(meme)}

Provide analysis as JSON.
"""

    # Create report from data
    return _create_report_from_data(sol_data)


def _create_report_from_data(sol_data: dict) -> SolanaDexReport:
    """Create report from data without LLM call."""
    spot = sol_data.get("spot_price", {})
    dex = sol_data.get("dex", {})
    meme = sol_data.get("meme", [])

    # SOL momentum
    change_24h = spot.get("change_24h_pct", 0)
    if change_24h > 5:
        sol_label = "bullish_24h"
    elif change_24h < -5:
        sol_label = "bearish_24h"
    else:
        sol_label = "neutral"

    # Meme liquidity assessment
    total_tvl = dex.get("total_tvl", 0)
    if total_tvl > 100_000_000:
        meme_liquidity = "high"
    elif total_tvl > 10_000_000:
        meme_liquidity = "medium"
    else:
        meme_liquidity = "low"

    # DEX rank (placeholder)
    dex_rank = "top_dex" if total_tvl > 50_000_000 else "secondary"

    # Confidence
    confidences = [spot.get("confidence", 0), dex.get("confidence", 0)]
    avg_conf = sum(c for c in confidences if c > 0) / max(len([c for c in confidences if c > 0]), 1)

    # Direction
    if change_24h > 3 and meme_liquidity in ("high", "medium"):
        direction = "bullish"
    elif change_24h < -5:
        direction = "bearish"
    else:
        direction = "neutral"

    return SolanaDexReport(
        summary=f"SOL {'bullish' if direction == 'bullish' else 'neutral'} - {sol_label}, meme liquidity {meme_liquidity}",
        direction=direction,
        confidence=avg_conf,
        signals=SolanaDexSignals(
            meme_liquidity={
                "value": meme_liquidity,
                "confidence": dex.get("confidence", 0.5),
            },
            meme_turnover={
                "value": 0.0,  # Placeholder
                "label": "normal",
                "confidence": 0.3,
            },
            sol_momentum={
                "value": change_24h,
                "label": sol_label,
                "confidence": spot.get("confidence", 0.5),
            },
            dex_volume_rank={
                "value": 1 if dex_rank == "top_dex" else 2,
                "label": dex_rank,
                "confidence": 0.5,
            },
        ),
        narrative=f"SOL price is ${spot.get('price_usd', 0):,.2f} ({change_24h:+.2f}% in 24h). "
                  f"DEX TVL is ${total_tvl:,.0f}. "
                  f"Meme liquidity assessment: {meme_liquidity}.",
    )
