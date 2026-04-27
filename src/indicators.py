"""
indicators.py — Technical indicator calculations for the VVV system.

All functions are pure: they accept a DataFrame and return a value or
an augmented DataFrame. No I/O, no side effects.
"""

import logging

import pandas as pd
import pandas_ta as ta

from src.config import VOL_SURGE_THRESHOLD

log = logging.getLogger(__name__)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute and attach all VVV indicators to an OHLCV DataFrame.

    Added columns:
      dma5, dma20          — 5 and 20-day simple moving averages of Close
      vol_ma20             — 20-day SMA of Volume
      vol_ratio            — Volume / vol_ma20
      rsi14                — 14-period RSI
      high_52w             — rolling max Close over last 252 bars
      pct_from_52w         — Close / high_52w  (1.0 = at 52w high)
      ret_1d               — 1-day return
      ret_5d               — 5-day return
    """
    df = df.copy()

    close  = df["Close"]
    volume = df["Volume"]

    df["dma5"]  = ta.sma(close, length=5)
    df["dma20"] = ta.sma(close, length=20)

    df["vol_ma20"] = ta.sma(volume.astype(float), length=20)
    df["vol_ratio"] = volume / df["vol_ma20"].replace(0, float("nan"))

    df["rsi14"] = ta.rsi(close, length=14)

    df["high_52w"]    = close.rolling(window=252, min_periods=20).max()
    df["pct_from_52w"] = close / df["high_52w"].replace(0, float("nan"))

    df["ret_1d"] = close.pct_change(1)
    df["ret_5d"] = close.pct_change(5)

    return df


def is_above_5dma(df: pd.DataFrame) -> bool:
    """True if the latest close is strictly above the latest 5DMA."""
    try:
        row = df.iloc[-1]
        return float(row["Close"]) > float(row["dma5"])
    except (KeyError, IndexError, ValueError):
        return False


def has_vol_surge(df: pd.DataFrame, threshold: float = VOL_SURGE_THRESHOLD) -> bool:
    """True if the latest session's volume is >= threshold × vol_ma20."""
    try:
        row = df.iloc[-1]
        return float(row["vol_ratio"]) >= threshold
    except (KeyError, IndexError, ValueError):
        return False


def pct_above_5dma(df: pd.DataFrame) -> float:
    """
    Percentage gap between the latest close and 5DMA.
    Positive → above 5DMA; negative → below 5DMA.
    """
    try:
        row = df.iloc[-1]
        dma5 = float(row["dma5"])
        if dma5 == 0:
            return 0.0
        return (float(row["Close"]) - dma5) / dma5 * 100
    except (KeyError, IndexError, ValueError):
        return 0.0


def latest_values(df: pd.DataFrame) -> dict:
    """Extract the most recent row as a plain dict (all indicators)."""
    if df.empty:
        return {}
    row = df.iloc[-1]
    return {
        "close":       round(float(row.get("Close", 0)), 2),
        "dma5":        round(float(row.get("dma5", 0)), 2),
        "dma20":       round(float(row.get("dma20", 0)), 2),
        "vol_ratio":   round(float(row.get("vol_ratio", 0)), 2),
        "rsi14":       round(float(row.get("rsi14", 0)), 1),
        "pct_from_52w": round(float(row.get("pct_from_52w", 0)), 4),
        "ret_1d":      round(float(row.get("ret_1d", 0)), 4),
        "ret_5d":      round(float(row.get("ret_5d", 0)), 4),
    }
