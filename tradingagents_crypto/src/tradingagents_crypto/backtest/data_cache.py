"""
Backtest Data Cache.

Manages historical candle and funding rate data for backtesting.
Uses Parquet format for efficient storage and retrieval.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".tradingagents" / "backtest_cache"


@dataclass
class DataGap:
    """Represents a gap in the data."""
    start: pd.Timestamp
    end: pd.Timestamp
    missing_bars: int


@dataclass
class GapCheckResult:
    """Result of checking for data gaps."""
    total_gaps: int
    total_missing_bars: int
    gaps: list[DataGap]
    completeness: float  # 0.0 to 1.0


class BacktestDataCache:
    """
    Manages historical data cache for backtesting.

    Storage format: Parquet files
    File naming: {symbol}_{interval}_{start}_{end}.parquet

    Features:
    - Automatic loading from cache
    - Gap detection and reporting
    - Support for multiple symbols and intervals
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the data cache.

        Args:
            cache_dir: Directory for cached files. Defaults to ~/.tradingagents/backtest_cache
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(
        self,
        symbol: str,
        interval: str,
        start: str,
        end: str,
    ) -> Path:
        """Get the cache file path for a dataset."""
        filename = f"{symbol}_{interval}_{start}_{end}.parquet"
        return self.cache_dir / filename

    def save_candles(
        self,
        candles: pd.DataFrame,
        symbol: str,
        interval: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Path:
        """
        Save candle data to cache.

        Args:
            candles: DataFrame with [timestamp, open, high, low, close, volume]
            symbol: Trading symbol (e.g., "BTC")
            interval: Time interval (e.g., "1h", "4h", "1d")
            start: Optional start date string
            end: Optional end date string

        Returns:
            Path to saved file
        """
        if start is None:
            start = str(candles["timestamp"].min().date()) if len(candles) > 0 else "unknown"
        if end is None:
            end = str(candles["timestamp"].max().date()) if len(candles) > 0 else "unknown"

        # Ensure timestamp is timezone-naive before saving
        candles = candles.copy()
        if candles["timestamp"].dt.tz is not None:
            candles["timestamp"] = candles["timestamp"].dt.tz_localize(None)
        elif candles["timestamp"].dt.tz_localize(None).dt.tz is not None:
            # Already tz-aware but we want naive
            candles["timestamp"] = candles["timestamp"].dt.tz_convert(None)

        path = self._get_cache_path(symbol, interval, start, end)
        candles.to_parquet(path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(candles)} candles to {path}")
        return path

    def load_candles(
        self,
        symbol: str,
        interval: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Load candle data from cache.

        Args:
            symbol: Trading symbol
            interval: Time interval
            start: Optional start date filter
            end: Optional end date filter

        Returns:
            DataFrame or None if not found
        """
        # Try to find any matching file
        if start and end:
            path = self._get_cache_path(symbol, interval, start, end)
            if path.exists():
                df = pd.read_parquet(path)
                return self._filter_by_date(df, start, end)

        # Search for any file matching symbol and interval
        pattern = f"{symbol}_{interval}_*.parquet"
        matching = list(self.cache_dir.glob(pattern))

        if not matching:
            return None

        # Load the most recent
        path = sorted(matching)[-1]
        df = pd.read_parquet(path)

        # Ensure timestamp column is datetime
        if df is not None and len(df) > 0:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return self._filter_by_date(df, start, end)

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start: Optional[str],
        end: Optional[str],
    ) -> pd.DataFrame:
        """Filter DataFrame by date range.

        Note: end is exclusive (standard filtering semantics).
        For hourly data with 48 bars spanning Jan 1-2:
        - start="2024-01-01", end="2024-01-02" returns only Jan 1st (~24 bars)
        """
        if df is None or len(df) == 0:
            return df

        if start:
            df = df[df["timestamp"] >= pd.to_datetime(start)]
        if end:
            df = df[df["timestamp"] < pd.to_datetime(end)]  # Exclusive on end

        return df

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start: str,
        end: str,
        data_loader: Optional[callable] = None,
    ) -> pd.DataFrame:
        """
        Get candles, loading from cache or API.

        Args:
            symbol: Trading symbol
            interval: Time interval
            start: Start date
            end: End date
            data_loader: Optional function to fetch data if not cached

        Returns:
            DataFrame with candle data
        """
        # Try cache first
        df = self.load_candles(symbol, interval, start, end)

        if df is not None and len(df) > 0:
            logger.info(f"Loaded {len(df)} candles from cache for {symbol}")
            return df

        # Fetch from API if loader provided
        if data_loader:
            logger.info(f"Fetching {symbol} candles from API...")
            df = data_loader(symbol=symbol, interval=interval, start=start, end=end)
            if df is not None and len(df) > 0:
                self.save_candles(df, symbol, interval, start, end)
                return df

        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    def save_funding_history(
        self,
        funding: pd.DataFrame,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Path:
        """
        Save funding rate history to cache.

        Args:
            funding: DataFrame with [timestamp, funding_rate]
            symbol: Trading symbol
            start: Optional start date
            end: Optional end date

        Returns:
            Path to saved file
        """
        if start is None:
            start = str(funding["timestamp"].min().date()) if len(funding) > 0 else "unknown"
        if end is None:
            end = str(funding["timestamp"].max().date()) if len(funding) > 0 else "unknown"

        # Ensure timestamp is timezone-naive before saving
        funding = funding.copy()
        if funding["timestamp"].dt.tz is not None:
            funding["timestamp"] = funding["timestamp"].dt.tz_localize(None)

        path = self.cache_dir / f"funding_{symbol}_{start}_{end}.parquet"
        funding.to_parquet(path, index=False)
        logger.info(f"Saved {len(funding)} funding records to {path}")
        return path

    def load_funding_history(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Load funding rate history from cache.

        Args:
            symbol: Trading symbol
            start: Optional start date filter
            end: Optional end date filter

        Returns:
            DataFrame or None if not found
        """
        pattern = f"funding_{symbol}_*.parquet"
        matching = list(self.cache_dir.glob(pattern))

        if not matching:
            return None

        path = sorted(matching)[-1]
        df = pd.read_parquet(path)

        # Ensure timestamp column is datetime
        if df is not None and len(df) > 0:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return self._filter_by_date(df, start, end)

    def get_funding_history(
        self,
        symbol: str,
        start: str,
        end: str,
        data_loader: Optional[callable] = None,
    ) -> pd.DataFrame:
        """
        Get funding history, loading from cache or API.

        Args:
            symbol: Trading symbol
            start: Start date
            end: End date
            data_loader: Optional function to fetch data

        Returns:
            DataFrame with [timestamp, funding_rate]
        """
        df = self.load_funding_history(symbol, start, end)

        if df is not None and len(df) > 0:
            logger.info(f"Loaded {len(df)} funding records from cache")
            return df

        if data_loader:
            logger.info(f"Fetching funding history from API...")
            df = data_loader(symbol=symbol, start=start, end=end)
            if df is not None and len(df) > 0:
                self.save_funding_history(df, symbol, start, end)
                return df

        return pd.DataFrame(columns=["timestamp", "funding_rate"])

    def check_gaps(self, df: pd.DataFrame, interval_hours: int = 1) -> GapCheckResult:
        """
        Check for gaps in time series data.

        Args:
            df: DataFrame with timestamp column
            interval_hours: Expected interval in hours (default 1h)

        Returns:
            GapCheckResult with gap information
        """
        if df is None or len(df) < 2:
            return GapCheckResult(
                total_gaps=0,
                total_missing_bars=0,
                gaps=[],
                completeness=1.0 if df is not None and len(df) > 0 else 0.0,
            )

        df = df.sort_values("timestamp").reset_index(drop=True)

        # Calculate expected intervals
        timestamps = pd.to_datetime(df["timestamp"])
        time_diffs = timestamps.diff()

        # Expected interval in seconds
        expected_seconds = interval_hours * 3600

        # Find gaps > 2x expected
        gap_mask = time_diffs > pd.Timedelta(seconds=expected_seconds * 2)
        gap_indices = gap_mask[gap_mask].index

        gaps = []
        total_missing = 0

        for idx in gap_indices:
            gap_start = timestamps.iloc[idx - 1]
            gap_end = timestamps.iloc[idx]
            diff_hours = (gap_end - gap_start).total_seconds() / 3600
            missing_bars = int(diff_hours / interval_hours) - 1

            if missing_bars > 0:
                gaps.append(DataGap(
                    start=gap_start,
                    end=gap_end,
                    missing_bars=missing_bars,
                ))
                total_missing += missing_bars

        total_expected = len(df) + total_missing
        completeness = len(df) / total_expected if total_expected > 0 else 0.0

        return GapCheckResult(
            total_gaps=len(gaps),
            total_missing_bars=total_missing,
            gaps=gaps,
            completeness=completeness,
        )

    def merge_candles(
        self,
        existing: pd.DataFrame,
        new: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge two candle DataFrames, removing duplicates.

        Args:
            existing: Existing DataFrame
            new: New DataFrame to merge

        Returns:
            Merged DataFrame with no duplicate timestamps
        """
        if existing is None or len(existing) == 0:
            return new
        if new is None or len(new) == 0:
            return existing

        combined = pd.concat([existing, new], ignore_index=True)
        combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
        combined = combined.sort_values("timestamp").reset_index(drop=True)

        return combined

    def clear_cache(self, symbol: Optional[str] = None) -> int:
        """
        Clear cached data.

        Args:
            symbol: Optional symbol to clear. If None, clears all.

        Returns:
            Number of files deleted
        """
        if symbol:
            pattern = f"*{symbol}*.parquet"
        else:
            pattern = "*.parquet"

        files = list(self.cache_dir.glob(pattern))
        for f in files:
            f.unlink()

        logger.info(f"Cleared {len(files)} cache files")
        return len(files)
