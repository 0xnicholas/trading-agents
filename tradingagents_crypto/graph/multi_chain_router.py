"""
Multi-chain router for Phase 2.

Routes analysis tasks to appropriate chain-specific analysts.
"""
__all__ = ['MultiChainRouter', 'create_multi_chain_graph']
import logging
from dataclasses import dataclass, field
from typing import Optional

from langgraph.graph import END, StateGraph, START

logger = logging.getLogger(__name__)


@dataclass
class MultiChainState:
    """State for multi-chain analysis workflow."""
    # Input
    user_request: str = ""
    symbol: str = "BTC"  # Primary symbol
    trade_date: str = ""

    # Routing
    chains_needed: list[str] = field(default_factory=list)  # ["eth", "sol", "btc"]
    analysis_type: str = "price"  # price, onchain, funding, dex, macro

    # Results
    tasks: list[dict] = field(default_factory=list)
    analyst_results: dict = field(default_factory=dict)
    aggregated_report: dict = field(default_factory=dict)
    status: str = "pending"


class MultiChainRouter:
    """Router for multi-chain analysis tasks."""

    # Chain detection keywords
    CHAIN_KEYWORDS = {
        "eth": ["eth", "ethereum", "ether", "erc20", "uniswap", "aave", "lido"],
        "sol": ["sol", "solana", "spl", "jupiter", "raydium", "orca", "pump.fun"],
        "btc": ["btc", "bitcoin", "₿", "ordinals", "runes"],
    }

    # Analysis type detection
    ANALYSIS_KEYWORDS = {
        "price": ["price", "chart", "technical", "support", "resistance"],
        "onchain": ["onchain", "on-chain", "whale", "wallet", "flow", "transfer"],
        "funding": ["funding", "rate", "perp", "perpetual", "basis"],
        "dex": ["dex", "liquidity", "amm", "swap", "pool", "lp"],
        "macro": ["macro", "market", "economy", "dominance", "sentiment", "fear"],
    }

    @classmethod
    def detect_chains(cls, request: str) -> list[str]:
        """Detect which chains are mentioned in the request."""
        request_lower = request.lower()
        chains = []

        for chain, keywords in cls.CHAIN_KEYWORDS.items():
            if any(kw in request_lower for kw in keywords):
                chains.append(chain)

        # Default to BTC if no specific chain mentioned
        if not chains:
            chains = ["btc"]

        return chains

    @classmethod
    def detect_analysis_type(cls, request: str) -> str:
        """Detect the type of analysis requested."""
        request_lower = request.lower()

        for analysis_type, keywords in cls.ANALYSIS_KEYWORDS.items():
            if any(kw in request_lower for kw in keywords):
                return analysis_type

        return "price"  # Default to price analysis

    @classmethod
    def route(cls, state: MultiChainState) -> MultiChainState:
        """Route the request to appropriate chains and analysis types."""
        request = state.user_request

        # Detect chains and analysis type
        chains = cls.detect_chains(request)
        analysis_type = cls.detect_analysis_type(request)

        state.chains_needed = chains
        state.analysis_type = analysis_type

        # Build tasks for each chain
        tasks = []
        for chain in chains:
            if chain == "btc":
                tasks.append({
                    "type": "btc_analysis",
                    "chain": "btc",
                    "analysis_type": analysis_type,
                    "priority": 1,
                    "symbol": "BTC",
                })
            elif chain == "eth":
                if analysis_type == "funding":
                    tasks.append({
                        "type": "eth_funding",
                        "chain": "eth",
                        "analysis_type": "funding",
                        "priority": 1,
                        "symbol": "ETH",
                    })
                elif analysis_type == "onchain":
                    tasks.append({
                        "type": "eth_onchain",
                        "chain": "eth",
                        "analysis_type": "onchain",
                        "priority": 1,
                        "symbol": "ETH",
                    })
                else:
                    tasks.append({
                        "type": "eth_analysis",
                        "chain": "eth",
                        "analysis_type": analysis_type,
                        "priority": 1,
                        "symbol": "ETH",
                    })
            elif chain == "sol":
                if analysis_type == "dex":
                    tasks.append({
                        "type": "sol_dex",
                        "chain": "sol",
                        "analysis_type": "dex",
                        "priority": 2,  # Lower priority than ETH/BTC
                        "symbol": "SOL",
                    })
                else:
                    tasks.append({
                        "type": "sol_analysis",
                        "chain": "sol",
                        "analysis_type": analysis_type,
                        "priority": 2,
                        "symbol": "SOL",
                    })

        # Always add macro analysis
        tasks.append({
            "type": "macro_analysis",
            "chain": "macro",
            "analysis_type": "macro",
            "priority": 1,
            "symbol": None,
        })

        state.tasks = tasks
        state.status = "routed"

        logger.info(
            "MultiChainRouter: %d chains, %d tasks: %s",
            len(chains), len(tasks), [t["type"] for t in tasks]
        )

        return state


def router_node(state: dict) -> dict:
    """Graph node: route request to appropriate chains."""
    multi_state = MultiChainState(
        user_request=state.get("user_request", ""),
        symbol=state.get("symbol", "BTC"),
        trade_date=state.get("trade_date", ""),
    )

    result = MultiChainRouter.route(multi_state)

    return {
        "chains_needed": result.chains_needed,
        "analysis_type": result.analysis_type,
        "tasks": result.tasks,
        "status": result.status,
    }


def create_multi_chain_graph():
    """Create the multi-chain routing graph.

    Returns:
        Compiled LangGraph workflow with multi-chain support
    """
    from tradingagents_crypto.graph.nodes.analyst_coordinator import (
        analyst_coordinator,
    )

    workflow = StateGraph(MultiChainState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("analyst_coordinator", analyst_coordinator)

    # Define edges
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "analyst_coordinator")
    workflow.add_edge("analyst_coordinator", END)

    return workflow.compile()
