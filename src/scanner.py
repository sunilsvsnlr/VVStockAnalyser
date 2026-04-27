"""
scanner.py — EOD breakout scanner (plan.md §4).

Criteria (each earns 1 point toward a 0–10 score):
  1. Close > 5DMA
  2. Close > 20DMA
  3. Volume >= 1.5× vol_ma20
  4. Volume >= 2.0× vol_ma20  (strong surge bonus)
  5. pct_from_52w >= 0.75     (within 25% of 52-week high)
  6. pct_from_52w >= 0.85     (near 52-week high bonus)
  7. RSI14 > 55
  8. RSI14 > 65               (strong momentum bonus)
  9. 1-day return > 1%
 10. 5-day return > 3%

Stocks with score < SCORE_MIN_FILTER are excluded from output.
"""

import logging

import pandas as pd

from src.config import (
    EQUITY_UNIVERSE,
    HIGH_52W_PCT,
    HIGH_52W_STRONG,
    RSI_STRONG,
    RSI_THRESHOLD,
    SCAN_LOOKBACK,
    SCORE_MIN_FILTER,
    VOL_SURGE_STRONG,
    VOL_SURGE_THRESHOLD,
)
from src.data_fetcher import get_historical
from src.indicators import add_indicators

log = logging.getLogger(__name__)


def _score_row(v: dict) -> int:
    """Compute breakout score (0–10) for a single row of indicator values."""
    score = 0

    if v["close"] > v["dma5"]:             score += 1
    if v["close"] > v["dma20"]:            score += 1
    if v["vol_ratio"] >= VOL_SURGE_THRESHOLD: score += 1
    if v["vol_ratio"] >= VOL_SURGE_STRONG:  score += 1
    if v["pct_from_52w"] >= HIGH_52W_PCT:   score += 1
    if v["pct_from_52w"] >= HIGH_52W_STRONG: score += 1
    if v["rsi14"] > RSI_THRESHOLD:          score += 1
    if v["rsi14"] > RSI_STRONG:             score += 1
    if v["ret_1d"] > 0.01:                  score += 1
    if v["ret_5d"] > 0.03:                  score += 1

    return score


def _signal_label(score: int) -> str:
    if score >= 9:
        return "MONSTER"
    if score >= 7:
        return "STRONG"
    if score >= 5:
        return "WATCH"
    return "-"


def run_scanner(universe: list[str] | None = None) -> pd.DataFrame:
    """
    Run the VVV breakout scan on the equity universe.

    Args:
        universe: list of yfinance symbols (e.g. ["MTAR.NS", ...]). Defaults
                  to EQUITY_UNIVERSE from config.

    Returns:
        DataFrame sorted by score descending, with columns:
          symbol, close, dma5, dma20, vol_ratio, rsi14,
          pct_from_52w, ret_1d, ret_5d, score, signal
        Only stocks with score >= SCORE_MIN_FILTER are returned.
    """
    if universe is None:
        universe = EQUITY_UNIVERSE

    log.info("Scanner: downloading %d symbols", len(universe))
    history = get_historical(universe, period="1y")

    rows = []
    for sym, df in history.items():
        if df is None or len(df) < 25:   # need at least 25 bars for indicators
            continue
        try:
            df = add_indicators(df)
            row = df.iloc[-1]

            v = {
                "close":       float(row.get("Close", 0)),
                "dma5":        float(row.get("dma5", 0)),
                "dma20":       float(row.get("dma20", 0)),
                "vol_ratio":   float(row.get("vol_ratio", 0)) if pd.notna(row.get("vol_ratio")) else 0.0,
                "rsi14":       float(row.get("rsi14", 0))     if pd.notna(row.get("rsi14"))     else 50.0,
                "pct_from_52w": float(row.get("pct_from_52w", 0)) if pd.notna(row.get("pct_from_52w")) else 0.0,
                "ret_1d":      float(row.get("ret_1d", 0))    if pd.notna(row.get("ret_1d"))    else 0.0,
                "ret_5d":      float(row.get("ret_5d", 0))    if pd.notna(row.get("ret_5d"))    else 0.0,
            }

            score = _score_row(v)
            if score < SCORE_MIN_FILTER:
                continue

            rows.append({
                "symbol":       sym.replace(".NS", ""),
                "close":        round(v["close"], 2),
                "dma5":         round(v["dma5"], 2),
                "dma20":        round(v["dma20"], 2),
                "vol_ratio":    round(v["vol_ratio"], 2),
                "rsi14":        round(v["rsi14"], 1),
                "pct_52w_high": f"{v['pct_from_52w'] * 100:.1f}%",
                "ret_1d":       f"{v['ret_1d'] * 100:.1f}%",
                "ret_5d":       f"{v['ret_5d'] * 100:.1f}%",
                "score":        score,
                "signal":       _signal_label(score),
            })

        except Exception as exc:
            log.debug("Scanner error for %s: %s", sym, exc)

    if not rows:
        return pd.DataFrame(columns=[
            "symbol", "close", "dma5", "dma20", "vol_ratio",
            "rsi14", "pct_52w_high", "ret_1d", "ret_5d", "score", "signal",
        ])

    result = pd.DataFrame(rows)
    result.sort_values("score", ascending=False, inplace=True)
    result.reset_index(drop=True, inplace=True)
    log.info("Scanner: %d breakout candidates (score >= %d)", len(result), SCORE_MIN_FILTER)
    return result
