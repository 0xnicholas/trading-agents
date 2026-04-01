"""
Crypto trading workflow graph.

LangGraph-based workflow for crypto trading decisions.
"""
from typing import Annotated
from dataclasses import dataclass

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph, START

from tradingagents_crypto.agents.base import AnalystReport, TradingDecision


@dataclass
class TradingState:
    """State for the crypto trading workflow."""
    symbol: str
    trade_date: str
    messages: list[BaseMessage]
    analyst_report: AnalystReport | None = None
    trading_decision: TradingDecision | None = None
    final_decision: str = "hold"


def create_crypto_trading_graph(llm, symbol: str):
    """
    Create the crypto trading workflow graph.

    Args:
        llm: LangChain LLM instance
        symbol: Symbol to trade (e.g., "BTC")

    Returns:
        Compiled LangGraph workflow
    """
    from tradingagents_crypto.agents.analysts.hyperliquid_perp_analyst import (
        create_analyst_node,
    )
    from tradingagents_crypto.agents.traders.crypto_trader import (
        create_trader_node,
    )

    # Create nodes (LLM passed at construction, captured in closure)
    analyst_node = create_analyst_node(symbol, llm)
    trader_node = create_trader_node(symbol, llm)

    # Build workflow
    workflow = StateGraph(TradingState)

    # Add nodes
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("trader", trader_node)

    # Set entry point
    workflow.add_edge(START, "analyst")

    # Analyst -> Trader
    workflow.add_edge("analyst", "trader")

    # Trader -> END
    workflow.add_edge("trader", END)

    return workflow.compile()


def run_trading_workflow(llm, symbol: str, trade_date: str = "") -> dict:
    """
    Run the complete trading workflow.

    Args:
        llm: LangChain LLM
        symbol: Symbol to trade
        trade_date: Optional date for backtest (YYYY-MM-DD)

    Returns:
        Final state with analyst report and trading decision
    """
    from datetime import datetime
    import pytz

    if not trade_date:
        tz = pytz.timezone("Asia/Shanghai")
        trade_date = datetime.now(tz).strftime("%Y-%m-%d")

    graph = create_crypto_trading_graph(llm, symbol)

    initial_state = {
        "symbol": symbol,
        "trade_date": trade_date,
        "messages": [],
    }

    result = graph.invoke(initial_state)
    return result