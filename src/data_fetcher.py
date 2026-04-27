"""
data_fetcher.py — Unified historical and live data acquisition.

Historical:  yfinance batch download (with per-symbol fallback)
Live quotes: Angel One SmartAPI during market hours, yfinance last close otherwise
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))

log = logging.getLogger(__name__)


def get_historical(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
) -> dict[str, pd.DataFrame]:
    """
    Download OHLCV history for a list of yfinance symbols.

    Returns {symbol: DataFrame(Open, High, Low, Close, Volume)}.
    Symbols that fail to download are silently omitted.
    """
    if not symbols:
        return {}

    results: dict[str, pd.DataFrame] = {}

    # Batch download (fast path)
    try:
        raw = yf.download(
            tickers=symbols,
            period=period,
            interval=interval,
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if not raw.empty:
            if len(symbols) == 1:
                # Single symbol — yfinance returns flat DataFrame
                df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
                if not df.empty:
                    results[symbols[0]] = df
            else:
                for sym in symbols:
                    try:
                        df = raw[sym][["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
                        if not df.empty:
                            results[sym] = df
                    except (KeyError, TypeError):
                        pass
    except Exception as exc:
        log.warning("Batch yfinance download failed (%s), falling back to per-symbol", exc)

    # Per-symbol fallback for anything that didn't make it through the batch
    missing = [s for s in symbols if s not in results]
    for sym in missing:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
            if df.empty:
                continue
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
            if not df.empty:
                results[sym] = df
        except Exception as exc:
            log.debug("yfinance per-symbol failed for %s: %s", sym, exc)

    return results


def get_live_quotes(symbols: list[str]) -> dict[str, dict]:
    """
    Return latest price data for each symbol.

    During market hours → Angel One SmartAPI (real-time LTP).
    Outside market hours  → yfinance last close.

    Returns {symbol: {ltp, open, high, low, close, volume}}.
    """
    if not symbols:
        return {}

    result: dict[str, dict] = {}

    # Try Angel One during market hours
    try:
        from references.angel_api import is_market_open
        from references.angel_api import get_live_quotes as angel_quotes

        if is_market_open():
            angel_result = angel_quotes(symbols, exchange="NSE")
            result.update(angel_result)
            log.debug("Angel One live quotes for %d symbols", len(angel_result))
    except Exception as exc:
        log.warning("Angel One live quote fetch failed: %s — using yfinance fallback", exc)

    # yfinance fallback for symbols not covered by Angel One (or outside hours)
    missing = [s for s in symbols if s not in result]
    if missing:
        hist = get_historical(missing, period="5d")
        for sym, df in hist.items():
            if df.empty:
                continue
            row = df.iloc[-1]
            result[sym] = {
                "ltp":    float(row["Close"]),
                "open":   float(row["Open"]),
                "high":   float(row["High"]),
                "low":    float(row["Low"]),
                "close":  float(row["Close"]),
                "volume": int(row["Volume"]),
            }

    return result
