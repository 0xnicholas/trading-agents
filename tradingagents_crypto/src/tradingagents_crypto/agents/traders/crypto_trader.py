"""
Crypto trader agent.

Makes trading decisions based on analyst reports.
"""
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import ValidationError

from tradingagents_crypto.agents.base import (
    CryptoAgentBase,
    AgentConfig,
    TradingDecision,
    AnalystReport,
)
from tradingagents_crypto.agents.schema import TradeSignal

logger = logging.getLogger(__name__)


TRADER_PROMPT = """You are a crypto trading decision agent.

Given an analyst's report on a symbol, you must make a clear trading decision.

## Available Actions
- **long**: Buy and hold a long position
- **short**: Open a short position
- **close**: Close any existing position
- **hold**: Do nothing, stay in cash

## Decision Factors
Consider:
1. **Direction & Confidence**: High confidence (>0.7) with clear direction → act on it
2. **Risk/Reward**: Is the potential gain worth the risk?
3. **Market Conditions**: What's the overall market doing?
4. **Position Sizing**: Based on confidence, how much to allocate?

## Position Sizing Guidelines
- Confidence 0.8-1.0: size_pct = 0.5-1.0 (aggressive)
- Confidence 0.6-0.8: size_pct = 0.25-0.5 (moderate)
- Confidence 0.4-0.6: size_pct = 0.1-0.25 (conservative)
- Confidence <0.4: size_pct = 0.0 (hold)

## Leverage Guidelines
- High confidence + low volatility: 10-20x
- Moderate confidence: 5-10x
- Uncertain/low confidence: 1-5x
- Never exceed 20x

## Risk Warnings
Flag any concerns:
- Extreme funding rates
- High volatility (ATR > 5%)
- OI exhaustion
- Imbalanced orderbook

Return a JSON object with:
{{
  "action": "long|short|close|hold",
  "size_pct": 0.0-1.0,
  "leverage": 1-20,
  "reason": "detailed reason for the decision",
  "risk_warnings": ["warning1", "warning2"]
}}
"""


class CryptoTrader:
    """
    Trader agent that makes decisions based on analyst reports.
    """

    def __init__(
        self,
        llm,
        symbol: str,
        config: AgentConfig | None = None,
    ):
        self.llm = llm
        self.symbol = symbol
        self.config = config or AgentConfig()

    def decide(self, analyst_report: AnalystReport) -> TradingDecision:
        """
        Make a trading decision based on an analyst report.

        Args:
            analyst_report: Report from HyperliquidPerpAnalyst

        Returns:
            TradingDecision with action, size, leverage, and reasoning
        """
        # Build the prompt
        prompt = f"""
Symbol: {self.symbol}

Analyst Report Summary:
{analyst_report.summary}

Direction: {analyst_report.direction}
Confidence: {analyst_report.confidence}

Key Metrics:
- Mark Price: {analyst_report.metrics.get('mark_price', 'N/A')}
- Funding Rate: {analyst_report.metrics.get('funding_rate', 'N/A')}
- Open Interest: ${analyst_report.metrics.get('open_interest_usd', 0):,.0f}
- RSI: {analyst_report.metrics.get('rsi', 'N/A')}
- MACD: {analyst_report.metrics.get('macd', 'N/A')}
- ATR: {analyst_report.metrics.get('atr', 'N/A')}

Signals:
{self._format_signals(analyst_report.signals)}

Narrative:
{analyst_report.narrative}

Based on the above analysis, make your trading decision.
"""

        messages = [
            SystemMessage(content=TRADER_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response with Pydantic validation
        import json
        import re

        json_match = re.search(r"\{[\s\S]*\}", content)
        validated_signal: TradeSignal | None = None

        if json_match:
            try:
                raw = json.loads(json_match.group())
                validated_signal = TradeSignal.model_validate(raw)
                logger.debug(f"Validated trade signal: {validated_signal.action}")
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Trade signal JSON parse/validation failed: {e}")

        if validated_signal is not None:
            warnings = list(validated_signal.risk_warnings) if validated_signal.risk_warnings else []
            if validated_signal.risk_adjusted:
                warnings.append("risk_adjusted")
            return TradingDecision(
                action=validated_signal.action,
                size_pct=validated_signal.size_pct,
                leverage=validated_signal.leverage,
                reason=validated_signal.entry_reason,
                risk_warnings=warnings,
            )

        # Fallback when JSON parsing failed
        logger.warning("LLM did not return valid trade signal JSON, defaulting to hold")
        return TradingDecision(
            action="hold",
            size_pct=0.0,
            leverage=1,
            reason=f"JSON parse failed. Raw response: {content[:200]}",
            risk_warnings=["parse_error"],
        )

    def _format_signals(self, signals: dict[str, Any]) -> str:
        """Format signals dict for prompt."""
        lines = []
        for key, value in signals.items():
            if isinstance(value, dict):
                lines.append(f"- {key}: {value}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No signals available."


def create_trader_node(symbol: str, llm):
    """
    Create a LangGraph node for the trader.

    Args:
        symbol: Symbol to trade
        llm: LangChain LLM instance (captured in closure)

    Returns:
        Node function for LangGraph
    """
    def trader_node(state: dict) -> dict:
        """
        Trader node for LangGraph.

        Expects state to have:
        - analyst_report: AnalystReport

        Returns state with trading_decision.
        """
        analyst_report = state.get("analyst_report")

        if analyst_report is None:
            return {
                "trading_decision": TradingDecision(
                    action="hold",
                    size_pct=0.0,
                    leverage=1,
                    reason="No analyst report available",
                ).to_dict()
            }

        trader = CryptoTrader(llm, symbol)
        decision = trader.decide(analyst_report)

        return {
            "trading_decision": decision.to_dict(),
        }

    return trader_node
