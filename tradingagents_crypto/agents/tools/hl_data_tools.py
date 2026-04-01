"""
Hyperliquid data tools for agents.

These tools provide structured market data to LLM agents.
"""
import logging
from datetime import datetime, timezone

from tradingagents_crypto.dataflows.hyperliquid.main import get_hl_data
from tradingagents_crypto.indicators.aggregator import compute_all_indicators, get_latest_indicators

logger = logging.getLogger(__name__)


def get_hl_market_data(symbol: str, date: str = "") -> str:
    """
    Get comprehensive Hyperliquid market data for a symbol.

    Retrieves and computes:
    - Candles (1h, 4h, 1d intervals)
    - Funding rate (current + annualized)
    - Open interest
    - Orderbook snapshot + imbalance
    - Technical indicators (RSI, MACD, Bollinger, MAs)

    Args:
        symbol: Coin name (e.g., "BTC", "ETH")
        date: Date string "YYYY-MM-DD" for backtest mode (optional)

    Returns:
        Formatted markdown string with all market data
    """
    try:
        data = get_hl_data(symbol, date or "2026-04-01")

        lines = [
            f"# {symbol} Market Data",
            "",
            f"## Funding Rate",
            f"- Rate (8h): `{data['funding']['funding_rate']:.6f}`",
            f"- Annualized: `{data['funding']['annualized']:.4f}` ({data['funding']['annualized']*100:.2f}%)",
            f"- Premium: `{data['funding']['premium']:.6f}`",
            "",
            f"## Open Interest",
            f"- OI: `${data['open_interest']['open_interest_usd']:,.0f}`",
            f"- Mark Price: `${data['open_interest']['mark_px']:,.2f}`",
            f"- Oracle Price: `${data['open_interest']['oracle_px']:,.2f}`",
            f"- 24h Volume: `${data['open_interest']['day_ntl_vlm']:,.0f}`",
            "",
            f"## Orderbook",
            f"- Bid Depth: {sum(s for _, s in data['orderbook']['bids']):.4f}",
            f"- Ask Depth: {sum(s for _, s in data['orderbook']['asks']):.4f}",
            f"- Imbalance: `{data['orderbook'].get('imbalance', 1.0):.4f}`",
            "",
        ]

        # Add 1h indicators
        candles_1h = data["candles"].get("1h")
        if candles_1h is not None and not candles_1h.empty:
            df_with_indicators = compute_all_indicators(candles_1h)
            latest = get_latest_indicators(df_with_indicators)

            lines.extend([
                f"## Technical Indicators (1h)",
                f"- RSI(14): `{latest.get('rsi', 0):.2f}`",
                f"- MACD: `{latest.get('macd', 0):.2f}` (signal: `{latest.get('macd_signal', 0):.2f}`)",
                f"- ATR: `{latest.get('atr', 0):.2f}` ({latest.get('atr_pct', 0):.2f}%)",
                f"- Bollinger: [{latest.get('boll_lower', 0):.2f} - {latest.get('boll_upper', 0):.2f}]",
                f"- MA7: `{latest.get('ma7', 0):.2f}`",
                f"- MA24: `{latest.get('ma24', 0):.2f}`",
                f"- MA50: `{latest.get('ma50', 0):.2f}`",
                f"- MA200: `{latest.get('ma200', 0):.2f}`",
                "",
            ])

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to get market data for {symbol}: {e}")
        return f"Error retrieving market data for {symbol}: {e}"


def get_funding_details(symbol: str) -> str:
    """
    Get detailed funding rate information.

    Args:
        symbol: Coin name (e.g., "BTC")

    Returns:
        Formatted markdown with funding details
    """
    from tradingagents_crypto.dataflows.hyperliquid.funding import get_current_funding, get_funding_history

    try:
        current = get_current_funding(symbol)
        history = get_funding_history(symbol, days=7)

        lines = [
            f"# {symbol} Funding Rate Details",
            "",
            f"## Current Funding",
            f"- 8h Rate: `{current['funding_rate']:.6f}` ({current['funding_rate']*100:.4f}%)",
            f"- Annualized: `{current['annualized']:.4f}` ({current['annualized']*100:.2f}%)",
            f"- Premium: `{current['premium']:.6f}`",
            "",
            f"## 7-Day Funding History",
        ]

        if history:
            lines.append("| Time | Rate | Premium |")
            lines.append("|------|------|--------|")
            for record in history[-8:]:  # Last 8 records
                time_str = datetime.fromtimestamp(
                    record.get("time", 0) / 1000,
                    tz=timezone.utc
                ).strftime("%m-%d %H:%M")
                rate = float(record.get("fundingRate", 0))
                prem = float(record.get("premium", 0))
                lines.append(f"| {time_str} | {rate:.6f} | {prem:.6f} |")
        else:
            lines.append("No funding history available.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to get funding details for {symbol}: {e}")
        return f"Error: {e}"


def get_orderbook_analysis(symbol: str, depth: int = 20) -> str:
    """
    Get orderbook analysis with imbalance calculation.

    Args:
        symbol: Coin name (e.g., "BTC")
        depth: Number of levels to analyze (default: 20)

    Returns:
        Formatted markdown with orderbook analysis
    """
    from tradingagents_crypto.dataflows.hyperliquid.orderbook import (
        get_orderbook,
        calc_orderbook_imbalance,
        calc_spread_bps,
    )

    try:
        ob = get_orderbook(symbol, depth=depth)
        imbalance = calc_orderbook_imbalance(ob)
        spread_bps = calc_spread_bps(ob)

        bid_depth = sum(size for _, size in ob["bids"])
        ask_depth = sum(size for _, size in ob["asks"])

        # Determine signal
        if imbalance > 1.2:
            signal = "🟢 BULLISH (more bids than asks)"
        elif imbalance < 0.8:
            signal = "🔴 BEARISH (more asks than bids)"
        else:
            signal = "⚪ NEUTRAL (balanced)"

        lines = [
            f"# {symbol} Orderbook Analysis",
            "",
            f"## Summary",
            f"- Best Bid: `{ob['bids'][0][0]:,.2f}` (size: {ob['bids'][0][1]:.4f})",
            f"- Best Ask: `{ob['asks'][0][0]:,.2f}` (size: {ob['asks'][0][1]:.4f})",
            f"- Spread: `{spread_bps:.2f}` bps",
            f"- Bid Depth: `{bid_depth:.4f}`",
            f"- Ask Depth: `{ask_depth:.4f}`",
            f"- Imbalance: `{imbalance:.4f}` → {signal}",
            "",
            f"## Top 5 Bids",
            f"| Level | Price | Size |",
            f"|-------|-------|------|",
        ]

        for i, (price, size) in enumerate(ob["bids"][:5]):
            lines.append(f"| {i+1} | {price:,.2f} | {size:.4f} |")

        lines.extend(["", f"## Top 5 Asks", "| Level | Price | Size |", "|-------|-------|------|"])
        for i, (price, size) in enumerate(ob["asks"][:5]):
            lines.append(f"| {i+1} | {price:,.2f} | {size:.4f} |")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Failed to get orderbook for {symbol}: {e}")
        return f"Error: {e}"


# Tool registry for agents
HYPERLIQUID_TOOLS = [
    get_hl_market_data,
    get_funding_details,
    get_orderbook_analysis,
]

__all__ = [
    "get_hl_market_data",
    "get_funding_details",
    "get_orderbook_analysis",
    "HYPERLIQUID_TOOLS",
]
