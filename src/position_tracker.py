"""
position_tracker.py — Open position management with 5DMA trailing stop (plan.md §6–7).

Each position is stored in positions.json:
  {"symbol": "MTARTECH.NS", "entry_price": 1500.0, "entry_date": "2026-04-01",
   "qty": 10, "notes": ""}

Status classification:
  HEALTHY  — close is > WARNING_PCT% above 5DMA  (let it run)
  WARNING  — close is 0 – WARNING_PCT% above 5DMA  (trail tightly)
  EXIT     — close is at or below 5DMA            (exit per plan rules)
"""

import json
import logging
from datetime import date

import pandas as pd

from src.config import POSITIONS_FILE, WARNING_PCT
from src.data_fetcher import get_historical, get_live_quotes
from src.indicators import add_indicators

log = logging.getLogger(__name__)

_STATUS_ORDER = {"EXIT": 0, "WARNING": 1, "HEALTHY": 2}


# ── Persistence ────────────────────────────────────────────────────────────────

def load_positions() -> list[dict]:
    """Load open positions from positions.json. Returns empty list if file absent."""
    if not POSITIONS_FILE.exists():
        return []
    try:
        with open(POSITIONS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        log.error("Failed to load positions.json: %s", exc)
        return []


def save_positions(positions: list[dict]) -> None:
    """Persist positions list to positions.json."""
    POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POSITIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2, default=str)


def add_position(symbol: str, entry_price: float, qty: int,
                 entry_date: str | None = None, notes: str = "") -> None:
    """Append a new position and save."""
    if not symbol.endswith(".NS"):
        symbol = symbol.upper() + ".NS"
    positions = load_positions()
    positions.append({
        "symbol":      symbol,
        "entry_price": float(entry_price),
        "qty":         int(qty),
        "entry_date":  entry_date or str(date.today()),
        "notes":       notes,
    })
    save_positions(positions)
    log.info("Position added: %s @ %.2f × %d", symbol, entry_price, qty)


def remove_position(symbol: str) -> bool:
    """Remove a position by symbol. Returns True if found and removed."""
    if not symbol.endswith(".NS"):
        symbol = symbol.upper() + ".NS"
    positions = load_positions()
    original_len = len(positions)
    positions = [p for p in positions if p["symbol"] != symbol]
    if len(positions) < original_len:
        save_positions(positions)
        log.info("Position removed: %s", symbol)
        return True
    return False


# ── Analysis ───────────────────────────────────────────────────────────────────

def _status(pct_gap: float) -> str:
    if pct_gap < 0:
        return "EXIT"
    if pct_gap < WARNING_PCT:
        return "WARNING"
    return "HEALTHY"


def check_positions(positions: list[dict] | None = None) -> pd.DataFrame:
    """
    Fetch latest data for each open position and return a status DataFrame.

    Columns:
      symbol, entry_price, qty, entry_date, notes,
      current_price, dma5, gap_to_5dma_pct,
      pnl_pct, pnl_abs, status
    """
    if positions is None:
        positions = load_positions()

    if not positions:
        return pd.DataFrame(columns=[
            "symbol", "entry_price", "qty", "entry_date", "notes",
            "current_price", "dma5", "gap_to_5dma_pct",
            "pnl_pct", "pnl_abs", "status",
        ])

    symbols = [p["symbol"] for p in positions]

    # Live prices (Angel One during market hours, yfinance otherwise)
    live = get_live_quotes(symbols)

    # Historical for 5DMA (need at least 10 days)
    hist = get_historical(symbols, period="30d")

    rows = []
    for pos in positions:
        sym = pos["symbol"]
        entry_price = float(pos.get("entry_price", 0))
        qty         = int(pos.get("qty", 0))

        # Current price — prefer live quote, fall back to last close in history
        current_price: float
        if sym in live:
            current_price = float(live[sym]["ltp"])
        elif sym in hist and not hist[sym].empty:
            current_price = float(hist[sym]["Close"].iloc[-1])
        else:
            log.warning("No price data for %s", sym)
            current_price = entry_price   # show neutral until data is available

        # 5DMA from history
        dma5 = float("nan")
        if sym in hist and not hist[sym].empty:
            df = add_indicators(hist[sym])
            dma5_val = df["dma5"].iloc[-1]
            if pd.notna(dma5_val):
                dma5 = float(dma5_val)

        # Derived metrics
        gap_pct = (current_price - dma5) / dma5 * 100 if not pd.isna(dma5) and dma5 != 0 else float("nan")
        pnl_pct = (current_price - entry_price) / entry_price * 100 if entry_price != 0 else 0.0
        pnl_abs = (current_price - entry_price) * qty

        rows.append({
            "symbol":         sym.replace(".NS", ""),
            "entry_price":    round(entry_price, 2),
            "qty":            qty,
            "entry_date":     pos.get("entry_date", ""),
            "notes":          pos.get("notes", ""),
            "current_price":  round(current_price, 2),
            "dma5":           round(dma5, 2) if not pd.isna(dma5) else None,
            "gap_to_5dma_pct": round(gap_pct, 2) if not pd.isna(gap_pct) else None,
            "pnl_pct":        round(pnl_pct, 2),
            "pnl_abs":        round(pnl_abs, 2),
            "status":         _status(gap_pct) if not pd.isna(gap_pct) else "UNKNOWN",
            "_sort_key":      _STATUS_ORDER.get(_status(gap_pct) if not pd.isna(gap_pct) else "HEALTHY", 2),
        })

    df = pd.DataFrame(rows)
    df.sort_values("_sort_key", inplace=True)
    df.drop(columns=["_sort_key"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
