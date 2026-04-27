"""
regime.py — Market regime filter (plan.md §2).

Checks Nifty50, Smallcap100, Midcap150 against their 5DMA and 20DMA to
classify the current market as GREEN / YELLOW / RED.

GREEN  — all 3 indices above both 5DMA and 20DMA  → new entries allowed
YELLOW — mixed signals                              → caution, reduce size
RED    — ≥2 indices below 5DMA or any below 20DMA → no new entries, exit weak positions
"""

import logging

import pandas as pd

from src.config import INDEX_TICKERS, REGIME_LOOKBACK
from src.data_fetcher import get_historical
from src.indicators import add_indicators

log = logging.getLogger(__name__)

_REGIME_COLORS = {
    "GREEN":  "#2ecc71",
    "YELLOW": "#f39c12",
    "RED":    "#e74c3c",
}

_REGIME_EMOJI = {
    "GREEN":  "🟢",
    "YELLOW": "🟡",
    "RED":    "🔴",
}


def _classify_index(close: float, dma5: float, dma20: float) -> str:
    """Return ABOVE_BOTH / ABOVE_5_BELOW_20 / BELOW_5."""
    if close > dma5 and close > dma20:
        return "ABOVE_BOTH"
    if close > dma5:
        return "ABOVE_5_BELOW_20"
    return "BELOW_5"


def get_regime() -> dict:
    """
    Fetch recent OHLCV for each index, compute 5DMA/20DMA, and determine regime.

    Returns:
    {
      "indices": {
        "NIFTY50": {
          "ticker": "^NSEI",
          "close": 22450.5,
          "dma5":  22100.0,
          "dma20": 21800.0,
          "status": "ABOVE_BOTH",   # or ABOVE_5_BELOW_20 / BELOW_5
          "pct_vs_5dma": 1.58,
        },
        ...
      },
      "regime":       "GREEN",
      "regime_color": "#2ecc71",
      "regime_emoji": "🟢",
      "detail":       "All indices above 5DMA & 20DMA",
      "above_count":  3,            # indices above 5DMA
      "below_count":  0,
    }
    """
    period = f"{REGIME_LOOKBACK + 10}d"   # a bit extra to cover weekends/holidays
    tickers = list(INDEX_TICKERS.values())
    history = get_historical(tickers, period=period)

    index_data: dict[str, dict] = {}

    for name, ticker in INDEX_TICKERS.items():
        df = history.get(ticker)
        if df is None or df.empty:
            log.warning("No data for index %s (%s)", name, ticker)
            index_data[name] = {
                "ticker": ticker,
                "close":  None,
                "dma5":   None,
                "dma20":  None,
                "status": "NO_DATA",
                "pct_vs_5dma": 0.0,
            }
            continue

        df = add_indicators(df)
        row = df.iloc[-1]

        close = float(row["Close"])
        dma5  = float(row["dma5"])  if pd.notna(row["dma5"])  else close
        dma20 = float(row["dma20"]) if pd.notna(row["dma20"]) else close

        status = _classify_index(close, dma5, dma20)
        pct_vs_5dma = (close - dma5) / dma5 * 100 if dma5 != 0 else 0.0

        index_data[name] = {
            "ticker":      ticker,
            "close":       round(close, 2),
            "dma5":        round(dma5, 2),
            "dma20":       round(dma20, 2),
            "status":      status,
            "pct_vs_5dma": round(pct_vs_5dma, 2),
        }

    # ── Regime classification (plan.md §2) ────────────────────────────────────
    statuses = [v["status"] for v in index_data.values() if v["status"] != "NO_DATA"]

    below_5_count    = statuses.count("BELOW_5")
    above_both_count = statuses.count("ABOVE_BOTH")
    total            = len(statuses)

    if total == 0:
        regime = "YELLOW"
        detail = "Could not fetch index data"
    elif below_5_count >= 2:
        regime = "RED"
        detail = f"{below_5_count} indices below 5DMA — stop new entries"
    elif any(v["status"] == "BELOW_5" for v in index_data.values()):
        regime = "YELLOW"
        detail = "One index below 5DMA — reduce size, no aggressive entries"
    elif any(v["status"] == "ABOVE_5_BELOW_20" for v in index_data.values()):
        regime = "YELLOW"
        detail = "Mixed signals — some indices between 5DMA and 20DMA"
    elif above_both_count == total:
        regime = "GREEN"
        detail = "All indices above 5DMA & 20DMA — new entries allowed"
    else:
        regime = "YELLOW"
        detail = "Partial confirmation"

    return {
        "indices":      index_data,
        "regime":       regime,
        "regime_color": _REGIME_COLORS[regime],
        "regime_emoji": _REGIME_EMOJI[regime],
        "detail":       detail,
        "above_count":  above_both_count,
        "below_count":  below_5_count,
    }
