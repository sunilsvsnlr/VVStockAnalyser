"""
config.py — Central configuration for the VVV NSE Swing Trading System.

Credentials are loaded from .env at project root:
  ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_TOTP_SECRET, ANGEL_MPIN
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Index tickers for market regime filter ─────────────────────────────────────
# yfinance symbols for NSE broad market indices
INDEX_TICKERS: dict[str, str] = {
    "NIFTY50":     "^NSEI",
    "SMALLCAP100": "^CNXSC",
    "MIDCAP150":   "^CNXMD",
}

# ── Scanner thresholds (from plan.md §4) ───────────────────────────────────────
VOL_SURGE_THRESHOLD: float = 1.5   # minimum volume/vol_ma20 ratio for breakout
VOL_SURGE_STRONG:    float = 2.0   # bonus tier
HIGH_52W_PCT:        float = 0.75  # close must be >= 75% of 52-week high
HIGH_52W_STRONG:     float = 0.85  # bonus tier
RSI_THRESHOLD:       float = 55.0
RSI_STRONG:          float = 65.0
SCORE_MIN_FILTER:    int   = 5     # stocks below this score excluded from output

REGIME_LOOKBACK: int = 30    # calendar days of data for regime calculation
SCAN_LOOKBACK:   int = 252   # trading days for 52-week high window

# ── Position tracker ───────────────────────────────────────────────────────────
WARNING_PCT:  float = 2.0   # % above 5DMA before WARNING status triggers
POSITIONS_FILE: Path = Path(__file__).parent.parent / "positions.json"

# ── Telegram ───────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID:   str = os.getenv("TELEGRAM_CHAT_ID", "")

# ── NSE equity universe ────────────────────────────────────────────────────────
# Liquid NSE mid/small-cap stocks (yfinance .NS suffix).
# Sourced from Nifty Midcap 150 / Smallcap 100 constituents.
# Extend or trim this list to suit your watchlist.
EQUITY_UNIVERSE: list[str] = [
    # VVV examples from plan.md
    "MTARTECH.NS", "POWERINDIA.NS", "BSE.NS", "NATIONALUM.NS", "AVANTIFEED.NS",
    "ATHERIND.NS",
    # Capital goods / industrials
    "BHEL.NS", "CUMMINSIND.NS", "ABB.NS", "SIEMENS.NS", "TIINDIA.NS",
    "GRINDWELL.NS", "APLAPOLLO.NS", "WELCORP.NS",
    # IT / Tech
    "PERSISTENT.NS", "COFORGE.NS", "KPITTECH.NS", "TATAELXSI.NS",
    "TANLA.NS", "MPHASIS.NS", "LTIM.NS", "OFSS.NS", "RATEGAIN.NS",
    # Chemicals / Pharma
    "LAURUS.NS", "ALKEM.NS", "DEEPAKNTR.NS", "AARTI.NS", "SUDARSCHEM.NS",
    "GRANULES.NS", "NAVINFLUOR.NS", "SOLARA.NS",
    # Consumer / Retail
    "KALYANKJIL.NS", "RAYMOND.NS", "BATAINDIA.NS", "VOLTAS.NS",
    "CERA.NS", "METROPOLIS.NS",
    # Power / Utilities
    "TORNTPOWER.NS", "NHPC.NS", "SJVN.NS",
    # Metals / Mining
    "NMDC.NS", "SAIL.NS",
    # Auto ancillaries
    "MOTHERSON.NS", "SONACOMS.NS", "UNOMINDA.NS",
    # Cables / Electricals
    "POLYCAB.NS", "KEI.NS", "HAVELLS.NS",
    # Financial services / AMC
    "HDFCAMC.NS", "ANGELONE.NS",
    # Logistics / Platforms
    "DELHIVERY.NS", "FSL.NS",
    # Semiconductors / Electronics
    "DIXON.NS", "AMBER.NS",
    # Paints / Adhesives
    "PIDILITIND.NS", "ASIANPAINT.NS",
    # FMCG
    "MARICO.NS", "DABUR.NS",
]
