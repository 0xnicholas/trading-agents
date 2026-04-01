"""
Hyperliquid unified data access.

Main entry point for getting all HL data for a symbol.
"""
import logging
import pandas as pd

from .api import HLClient
from .cache import CacheManager
from .candles import get_candles
from .funding import get_current_funding
from .oi import get_open_interest
from .orderbook import get_orderbook, calc_orderbook_imbalance

logger = logging.getLogger(__name__)


def get_hl_data(
    symbol: str,
    date: str,
    intervals: list[str] | None = None,
    client: HLClient | None = None,
    cache: CacheManager | None = None,
    backtest_mode: bool = False,
) -> dict:
    """
    Get all Hyperliquid data for a symbol.

    Args:
        symbol: Coin name (e.g., "BTC", "ETH")
        date: Date string "YYYY-MM-DD" (used for backtest mode filtering)
        intervals: List of candle intervals (default: ["1h", "4h", "1d"])
        client: Optional HLClient instance
        cache: Optional CacheManager instance
        backtest_mode: If True, filter data by date

    Returns:
        Dict with keys:
        - symbol: Symbol name
        - candles: Dict[interval -> DataFrame]
        - funding: Dict with funding data
        - open_interest: Dict with OI data
        - orderbook: Dict with orderbook data
    """
    if intervals is None:
        intervals = ["1h", "4h", "1d"]

    if client is None:
        client = HLClient()
    if cache is None:
        cache = CacheManager()

    # Determine days for each interval
    days_map = {
        "1h": 7,
        "4h": 7,
        "1d": 30,
    }

    # Fetch candles for each interval
    candles = {}
    for interval in intervals:
        days = days_map.get(interval, 7)
        try:
            df = get_candles(
                symbol, interval, days,
                client=client, cache=cache
            )

            # Apply date filter in backtest mode
            if backtest_mode and date:
                df = filter_by_date(df, date)

            candles[interval] = df
        except Exception as e:
            logger.warning(
                f"Failed to get {symbol} {interval} candles: {e}"
            )
            candles[interval] = pd.DataFrame()

    # Fetch funding rate
    try:
        funding = get_current_funding(symbol, client=client, cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get funding for {symbol}: {e}")
        funding = {"funding_rate": 0.0, "annualized": 0.0}

    # Fetch open interest
    try:
        oi_data = get_open_interest(symbol, client=client, cache=cache)
    except Exception as e:
        logger.warning(f"Failed to get OI for {symbol}: {e}")
        oi_data = {"open_interest_usd": 0.0}

    # Fetch orderbook (no caching)
    try:
        orderbook = get_orderbook(symbol, client=client)
        orderbook["imbalance"] = calc_orderbook_imbalance(orderbook)
    except Exception as e:
        logger.warning(f"Failed to get orderbook for {symbol}: {e}")
        orderbook = {"coin": symbol, "bids": [], "asks": [], "imbalance": 1.0}

    return {
        "symbol": symbol,
        "candles": candles,
        "funding": funding,
        "open_interest": oi_data,
        "orderbook": orderbook,
    }


def filter_by_date(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    Filter DataFrame to only include data on or before date.

    Args:
        df: DataFrame with 'timestamp' column (Unix seconds)
        date: Date string "YYYY-MM-DD"

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    import datetime
    try:
        cutoff = datetime.datetime.strptime(date, "%Y-%m-%d")
        cutoff_ts = int(cutoff.timestamp())
        original_len = len(df)
        filtered = df[df["timestamp"] <= cutoff_ts]
        if len(filtered) < original_len:
            logger.info(
                f"Backtest filter: {date} -> kept {len(filtered)}/{original_len} candles"
            )
        if len(filtered) == 0:
            logger.warning(
                f"Backtest filter: date {date} is after all data, returning empty DataFrame"
            )
        return filtered
    except ValueError as e:
        logger.error(f"Invalid date format '{date}': {e}. Expected YYYY-MM-DD. Returning unfiltered data.")
        return df
    except Exception as e:
        logger.error(f"Unexpected error filtering by date '{date}': {e}. Returning unfiltered data.")
        return df
