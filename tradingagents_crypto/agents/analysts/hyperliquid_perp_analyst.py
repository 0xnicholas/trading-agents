"""
Hyperliquid Perpetual Analyst.

Analyzes Hyperliquid perpetuals using on-chain and market data.
"""
import logging
from typing import Annotated

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from tradingagents_crypto.agents.base import (
    CryptoAgentBase,
    AgentConfig,
    AnalystReport,
)
from tradingagents_crypto.agents.tools.hl_data_tools import (
    get_hl_market_data,
    get_funding_details,
    get_orderbook_analysis,
)
from tradingagents_crypto.agents.schema import HyperliquidPerpReport

logger = logging.getLogger(__name__)


# Default system prompt for the Hyperliquid analyst
HYPERLIQUID_ANALYST_PROMPT = """You are an expert analyst specializing in Hyperliquid perpetuals trading.

Your role is to analyze {symbol} on Hyperliquid and provide a comprehensive trading analysis.

## Available Data
You have access to real-time Hyperliquid data including:
- Candles (1h, 4h, 1d intervals) with technical indicators
- Funding rates (current + historical)
- Open interest and volume
- Orderbook depth and imbalance
- On-chain context (mark price, oracle price, premium)

## Your Task
1. Use the provided tools to gather all relevant data
2. Analyze the data holistically
3. Generate a detailed report with:
   - Clear direction (bullish/bearish/neutral)
   - Confidence level (0.0-1.0)
   - Key signals and metrics
   - A narrative explanation

## Analysis Framework
Consider:
1. **Funding Rate**: Is it positive/negative? High/low? This indicates market sentiment.
2. **Open Interest**: Is OI expanding or contracting? Rising OI with rising price = bullish confirmation.
3. **Orderbook Imbalance**: Are there more bids or asks? Large imbalance can signal reversal.
4. **Technical Indicators**:
   - RSI > 70 = overbought, RSI < 30 = oversold
   - MACD cross above signal = bullish momentum
   - Price above MA200 = long-term bullish
5. **Volatility**: High ATR% may indicate upcoming moves

## Output Format
Your final report MUST:
1. Start with a 1-2 sentence summary
2. State clear direction and confidence
3. Detail all signals (bullish/bearish/neutral)
4. Provide specific metrics
5. Explain your reasoning

Be precise and quantitative. Use numbers, not vague terms.
"""


def create_hyperliquid_analyst(
    llm,
    symbol: str,
    config: AgentConfig | None = None,
) -> CryptoAgentBase:
    """
    Create a Hyperliquid Perp analyst agent.

    Args:
        llm: LangChain LLM instance
        symbol: Symbol to analyze (e.g., "BTC", "ETH")
        config: Optional agent configuration

    Returns:
        CryptoAgentBase configured for Hyperliquid analysis
    """
    if config is None:
        config = AgentConfig(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=4096,
        )

    tools = [get_hl_market_data, get_funding_details, get_orderbook_analysis]

    agent = CryptoAgentBase(
        name=f"HyperliquidPerpAnalyst-{symbol}",
        description=f"Expert analyst for {symbol} on Hyperliquid",
        tools=tools,
        config=config,
    )

    agent.symbol = symbol
    return agent


def analyze_hyperliquid_perp(
    symbol: str,
    llm,
    date: str = "",
    config: AgentConfig | None = None,
) -> AnalystReport:
    """
    Run a complete Hyperliquid analysis for a symbol.

    Args:
        symbol: Coin to analyze (e.g., "BTC")
        llm: LangChain LLM
        date: Optional date for backtest mode (YYYY-MM-DD)
        config: Optional agent configuration

    Returns:
        AnalystReport with full analysis
    """
    if config is None:
        config = AgentConfig()

    # Get market data
    market_data = get_hl_market_data(symbol, date)
    funding_details = get_funding_details(symbol)
    orderbook = get_orderbook_analysis(symbol, depth=20)

    # Build analysis prompt
    prompt = f"""
Analyze {symbol} on Hyperliquid based on the following data:

=== MARKET DATA ===
{market_data}

=== FUNDING DETAILS ===
{funding_details}

=== ORDERBOOK ANALYSIS ===
{orderbook}

## Your Analysis Task

Based on ALL the data above, provide a comprehensive analysis of {symbol}.

Generate a JSON object with this exact structure:
{{
  "summary": "1-2 sentence summary of the trade",
  "direction": "bullish | bearish | neutral",
  "confidence": 0.0-1.0,
  "signals": {{
    "funding_rate": {{"value": rate, "annualized": pct, "verdict": "normal|elevated|extreme"}},
    "oi_trend": {{"current": usd, "change_pct": pct, "verdict": "bullish|bearish|neutral"}},
    "orderbook_imbalance": {{"ratio": float, "verdict": "bullish|bearish|neutral"}},
    "volume_anomaly": {{"ratio": float, "verdict": "normal|elevated|anomalous"}},
    "volatility": {{"atr_pct": float, "position": "low|medium|high|extreme"}},
    "trend_4h": {{"direction": "bullish|bearish|neutral", "ma_cross": "above_ma|below_ma"}},
    "trend_1d": {{"direction": "bullish|bearish|neutral", "ma_cross": "above_ma|below_ma"}}
  }},
  "metrics": {{
    "mark_price": float,
    "index_price": float,
    "funding_rate": float,
    "open_interest_usd": float,
    "volume_24h": float,
    "rsi": float,
    "atr": float,
    "macd": float,
    "macd_signal": float,
    "boll_upper": float,
    "boll_lower": float
  }},
  "narrative": "Detailed paragraph explaining the analysis and reasoning"
}}

Be precise with numbers. confidence should reflect conviction level.
"""

    messages = [
        SystemMessage(content=HYPERLIQUID_ANALYST_PROMPT.format(symbol=symbol)),
        HumanMessage(content=prompt),
    ]

    # Invoke LLM
    response = llm.invoke(messages)

    # Parse response
    content = response.content if hasattr(response, "content") else str(response)

    # Try to extract JSON from the response
    import json
    import re

    # Look for JSON block
    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response")
            parsed = {
                "summary": content[:200],
                "direction": "neutral",
                "confidence": 0.5,
                "signals": {},
                "metrics": {},
                "narrative": content,
            }
    else:
        parsed = {
            "summary": content[:200],
            "direction": "neutral",
            "confidence": 0.5,
            "signals": {},
            "metrics": {},
            "narrative": content,
        }

    return AnalystReport(
        summary=parsed.get("summary", ""),
        direction=parsed.get("direction", "neutral"),
        confidence=parsed.get("confidence", 0.5),
        signals=parsed.get("signals", {}),
        metrics=parsed.get("metrics", {}),
        narrative=parsed.get("narrative", ""),
    )


def create_analyst_node(symbol: str, llm):
    """
    Create a LangGraph node function for the analyst.

    Use this in a LangGraph workflow.

    Args:
        symbol: Symbol to analyze
        llm: LangChain LLM instance (captured in closure)

    Returns:
        Node function that takes state and returns updated state
    """
    def analyst_node(state: dict) -> dict:
        """
        Analyst node for LangGraph.

        Expects state to have:
        - symbol: str
        - trade_date: str
        - messages: list

        Returns state with updated messages and analyst_report.
        """
        current_date = state.get("trade_date", "")
        messages = state.get("messages", [])

        # Get market data
        market_data = get_hl_market_data(
            symbol, current_date, backtest_mode=bool(current_date)
        )
        funding_details = get_funding_details(symbol)
        orderbook = get_orderbook_analysis(symbol, depth=20)

        # Build analysis request
        analysis_prompt = f"""
Analyze {symbol} using the data provided below.

=== MARKET DATA ===
{market_data}

=== FUNDING DETAILS ===
{funding_details}

=== ORDERBOOK ===
{orderbook}

Provide your analysis as a JSON object with:
- summary (1-2 sentences)
- direction (bullish/bearish/neutral)
- confidence (0.0-1.0)
- narrative (detailed reasoning)

Return ONLY the JSON, no additional text.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", HYPERLIQUID_ANALYST_PROMPT.format(symbol=symbol)),
            MessagesPlaceholder(variable_name="messages"),
            ("human", analysis_prompt),
        ])

        chain = prompt | llm
        result = chain.invoke({"messages": messages})

        return {
            "messages": [result],
            "analyst_report": result.content if hasattr(result, "content") else str(result),
        }

    return analyst_node
