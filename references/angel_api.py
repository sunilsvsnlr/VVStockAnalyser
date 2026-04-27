"""
angel_api.py — Angel One SmartAPI integration for NSE Options trading.

Adapted from StockAnalyst/src/angel_api.py with NFO segment extensions:
  - Reused: credential loading, session management, market hours, live quotes
  - Added:  NFO token map, live option quotes, place/cancel option orders,
            positions, order book

Public API:
  is_market_open()                          -> bool
  get_session()                             -> (SmartConnect, token)
  get_live_quotes(symbols, exchange)        -> dict
  get_nfo_token_map(symbols)               -> dict {symbol: token}
  get_live_option_price(tokens)            -> dict {token: ltp}
  place_option_order(symbol, token, qty, side, order_type, price) -> str (order_id)
  cancel_order(order_id, variety)          -> bool
  get_positions()                          -> list[dict]
  get_order_book()                         -> list[dict]
"""

import json
import logging
import time
import urllib.request
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Optional

import pyotp

log = logging.getLogger(__name__)


# ── Credential loading ─────────────────────────────────────────────────────────

def _load_env() -> dict:
    """Load credentials from .env file in project root."""
    env_path = Path(__file__).parent.parent / ".env"
    creds = {}
    if not env_path.exists():
        raise FileNotFoundError(f".env not found at {env_path}")
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                creds[key.strip()] = val.strip()
    required = ["ANGEL_API_KEY", "ANGEL_CLIENT_ID", "ANGEL_TOTP_SECRET"]
    missing = [k for k in required if not creds.get(k) or "YOUR_" in creds.get(k, "")]
    if missing:
        raise ValueError(f"Missing credentials in .env: {missing}")
    return creds


# ── Session management ────────────────────────────────────────────────────────

_session_cache: dict = {}


def _get_totp(secret: str) -> str:
    return pyotp.TOTP(secret).now()


def get_session(force_new: bool = False):
    """
    Return an authenticated SmartConnect session.
    Caches for ~8 hours to avoid repeated logins.
    """
    global _session_cache
    now = time.time()
    if not force_new and _session_cache.get("expiry", 0) > now:
        return _session_cache["obj"], _session_cache["token"]

    from SmartApi import SmartConnect

    creds       = _load_env()
    api_key     = creds["ANGEL_API_KEY"]
    client_id   = creds["ANGEL_CLIENT_ID"]
    totp_secret = creds["ANGEL_TOTP_SECRET"]
    mpin        = creds.get("ANGEL_MPIN") or creds.get("ANGEL_PASSWORD", "")

    obj  = SmartConnect(api_key=api_key)
    totp = _get_totp(totp_secret)
    data = obj.generateSession(client_id, mpin, totp)

    if not data or data.get("status") is False:
        msg = data.get("message", "Unknown error") if data else "No response"
        raise ConnectionError(f"Angel SmartAPI login failed: {msg}")

    auth_token = data["data"]["jwtToken"]
    _session_cache = {
        "obj":    obj,
        "token":  auth_token,
        "expiry": now + 8 * 3600,
    }
    log.info("Angel SmartAPI session created for %s", client_id)
    return obj, auth_token


# ── Instrument master ─────────────────────────────────────────────────────────

_INSTRUMENT_URL  = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
_NSE_CACHE       = Path(__file__).parent.parent / "data" / "angel_instruments.json"
_NFO_CACHE       = Path(__file__).parent.parent / "data" / "instruments_nfo.json"
_CACHE_HOURS     = 24

_nse_token_map: dict = {}
_nfo_token_map: dict = {}   # {SYMBOL_EXPIRY_STRIKE_TYPE: token}
_nfo_instruments: list = []


def _download_instruments() -> list:
    """Download Angel full instrument master."""
    log.info("Downloading Angel instrument master...")
    req = urllib.request.Request(_INSTRUMENT_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


def _load_instruments() -> list:
    """Load from disk cache if fresh, else re-download."""
    cache = _NSE_CACHE
    if cache.exists():
        age_hours = (time.time() - cache.stat().st_mtime) / 3600
        if age_hours < _CACHE_HOURS:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)

    instruments = _download_instruments()
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(instruments, f)
    log.info("Instrument master cached: %d entries", len(instruments))
    return instruments


def get_nfo_instruments() -> list:
    """
    Return all NFO (F&O) instruments from the Angel instrument master.
    Each entry is a dict with keys: symbol, token, name, expiry, strike, optiontype, lotsize, exch_seg
    """
    global _nfo_instruments

    if _nfo_instruments:
        return _nfo_instruments

    # Check NFO-specific cache
    if _NFO_CACHE.exists():
        age_hours = (time.time() - _NFO_CACHE.stat().st_mtime) / 3600
        if age_hours < _CACHE_HOURS:
            with open(_NFO_CACHE, encoding="utf-8") as f:
                _nfo_instruments = json.load(f)
                return _nfo_instruments

    all_instruments = _load_instruments()
    nfo = [i for i in all_instruments if i.get("exch_seg") == "NFO"]

    _NFO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(_NFO_CACHE, "w", encoding="utf-8") as f:
        json.dump(nfo, f)

    _nfo_instruments = nfo
    log.info("NFO instruments cached: %d entries", len(nfo))
    return _nfo_instruments


def get_nfo_token_map(index_symbol: str, expiry_str: str) -> dict:
    """
    Build a token map for all options of a given index and expiry.

    Args:
        index_symbol: "NIFTY" or "BANKNIFTY"
        expiry_str:   Expiry in Angel format, e.g. "25MAR2026" (ddMMMYYYY)

    Returns:
        {
          "NIFTY25MAR2026CE24000": {"token": "...", "strike": 24000.0, "opt_type": "CE"},
          ...
        }
    """
    nfo = get_nfo_instruments()
    result = {}

    for item in nfo:
        name = item.get("name", "").upper()
        if name != index_symbol.upper():
            continue
        expiry = item.get("expiry", "").upper()
        if expiry != expiry_str.upper():
            continue

        # instrumenttype is "OPTIDX" — extract CE/PE from symbol suffix
        if item.get("instrumenttype", "").upper() != "OPTIDX":
            continue
        sym_str = item.get("symbol", "")
        if sym_str.endswith("CE"):
            opt_type = "CE"
        elif sym_str.endswith("PE"):
            opt_type = "PE"
        else:
            continue

        strike = float(item.get("strike", 0)) / 100  # Angel stores strike × 100
        token  = item.get("token", "")

        result[sym_str] = {
            "token":    token,
            "strike":   strike,
            "opt_type": opt_type,
            "lotsize":  int(item.get("lotsize", 1)),
            "expiry":   expiry,
        }

    return result


def get_available_expiries(index_symbol: str) -> list:
    """
    Return sorted list of available expiry date strings for a given index
    directly from the Angel instrument master (e.g. ["17MAR2026", "24MAR2026"]).
    """
    nfo = get_nfo_instruments()
    expiries = sorted(set(
        item["expiry"]
        for item in nfo
        if item.get("name", "").upper() == index_symbol.upper()
        and item.get("instrumenttype", "").upper() == "OPTIDX"
        and item.get("expiry", "")
    ))
    return expiries


# ── Market hours ──────────────────────────────────────────────────────────────

def is_market_open() -> bool:
    """Return True if NSE is currently open (Mon-Fri, 9:15-15:30 IST)."""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return dtime(9, 15) <= now.time() <= dtime(15, 30)


# ── Live quote fetching ───────────────────────────────────────────────────────

def get_live_quotes(symbols: list, exchange: str = "NSE") -> dict:
    """
    Fetch live quotes for NSE EQ symbols.
    Returns {symbol: {ltp, open, high, low, close, volume}}
    """
    if not symbols:
        return {}

    instruments = _load_instruments()
    exch_map = {
        item["symbol"].upper(): item["token"]
        for item in instruments
        if item.get("exch_seg") == exchange
    }

    clean = [s.replace(".NS", "").upper() for s in symbols]
    token_map = {s: exch_map[s] for s in clean if s in exch_map}

    if not token_map:
        return {}

    obj, _ = get_session()
    tokens = list(token_map.values())
    raw = {}

    for i in range(0, len(tokens), 500):
        batch = tokens[i: i + 500]
        try:
            resp = obj.getMarketData(mode="FULL", exchangeTokens={exchange: batch})
            if resp and resp.get("status") and resp.get("data"):
                for q in resp["data"].get("fetched", []):
                    raw[q["symbolToken"]] = q
        except Exception as exc:
            log.warning("getMarketData batch failed: %s", exc)

    token_to_sym = {v: k for k, v in token_map.items()}
    result = {}
    for token, q in raw.items():
        sym = token_to_sym.get(token)
        if not sym:
            continue
        try:
            result[sym] = {
                "ltp":    float(q.get("ltp", 0)),
                "open":   float(q.get("open", 0)),
                "high":   float(q.get("high", 0)),
                "low":    float(q.get("low", 0)),
                "close":  float(q.get("close", 0)),
                "volume": int(q.get("tradeVolume", q.get("volume", 0))),
            }
        except (TypeError, ValueError) as e:
            log.debug("Quote parse error %s: %s", sym, e)

    return result


def get_live_option_prices(tokens: list) -> dict:
    """
    Fetch LTP for a list of NFO option tokens.

    Args:
        tokens: list of Angel token strings (NFO segment)

    Returns:
        {token: ltp_float}
    """
    if not tokens:
        return {}

    obj, _ = get_session()
    result = {}

    NFO_BATCH = 50   # Angel One NFO segment limit per request
    for i in range(0, len(tokens), NFO_BATCH):
        batch = tokens[i: i + NFO_BATCH]
        try:
            resp = obj.getMarketData(mode="LTP", exchangeTokens={"NFO": batch})
            if resp and resp.get("status") and resp.get("data"):
                for q in resp["data"].get("fetched", []):
                    tok = q.get("symbolToken", "")
                    ltp = q.get("ltp", 0)
                    if tok:
                        result[tok] = float(ltp)
        except Exception as exc:
            log.warning("NFO option price fetch failed: %s", exc)

    return result


# ── Order management ──────────────────────────────────────────────────────────

def place_option_order(
    tradingsymbol: str,
    token: str,
    qty: int,
    side: str,        # "BUY" or "SELL"
    order_type: str = "LIMIT",
    price: float = 0.0,
    variety: str = "NORMAL",
    dry_run: bool = True,
) -> Optional[str]:
    """
    Place an NSE F&O option order via Angel SmartAPI.

    Args:
        tradingsymbol: Angel NFO symbol, e.g. "NIFTY25MAR2026CE24000"
        token:         Angel token for the symbol
        qty:           Quantity in lots (Angel API expects number of shares = lots × lotsize)
        side:          "BUY" or "SELL"
        order_type:    "LIMIT", "MARKET", "SL", "SL-M"
        price:         Limit price (0 for market orders)
        variety:       "NORMAL", "STOPLOSS", "AMO"
        dry_run:       If True, log order without placing (paper trade mode)

    Returns:
        order_id string if successful, None on failure
    """
    order_params = {
        "variety":         variety,
        "tradingsymbol":   tradingsymbol,
        "symboltoken":     token,
        "transactiontype": side.upper(),
        "exchange":        "NFO",
        "ordertype":       order_type.upper(),
        "producttype":     "CARRYFORWARD",   # MIS for intraday, CARRYFORWARD for overnight
        "duration":        "DAY",
        "quantity":        str(qty),
        "price":           str(round(price, 1)),
        "triggerprice":    "0",
        "squareoff":       "0",
        "stoploss":        "0",
    }

    if dry_run:
        log.info("[DRY RUN] Would place order: %s", order_params)
        return f"DRY-{int(time.time())}"

    try:
        obj, _ = get_session()
        resp = obj.placeOrder(order_params)
        if resp and resp.get("status"):
            order_id = resp["data"]["orderid"]
            log.info("Order placed: %s %s %s qty=%d price=%.1f → id=%s",
                     side, tradingsymbol, order_type, qty, price, order_id)
            return order_id
        else:
            msg = resp.get("message", "Unknown") if resp else "No response"
            log.error("Order placement failed: %s", msg)
            return None
    except Exception as exc:
        log.error("place_option_order exception: %s", exc)
        return None


def cancel_order(order_id: str, variety: str = "NORMAL") -> bool:
    """Cancel an open order. Returns True on success."""
    try:
        obj, _ = get_session()
        resp = obj.cancelOrder(order_id, variety)
        if resp and resp.get("status"):
            log.info("Order cancelled: %s", order_id)
            return True
        log.warning("Cancel failed for %s: %s", order_id, resp)
        return False
    except Exception as exc:
        log.error("cancel_order exception: %s", exc)
        return False


def get_positions() -> list:
    """
    Fetch all open F&O positions from Angel One.

    Returns list of position dicts with keys:
    symbolname, tradingsymbol, netqty, avgnetprice, unrealised, realised, exchange, etc.
    """
    try:
        obj, _ = get_session()
        resp = obj.position()
        if resp and resp.get("status") and resp.get("data"):
            return resp["data"] or []
        return []
    except Exception as exc:
        log.error("get_positions failed: %s", exc)
        return []


def get_order_book() -> list:
    """
    Fetch today's order book from Angel One.
    Returns list of order dicts.
    """
    try:
        obj, _ = get_session()
        resp = obj.orderBook()
        if resp and resp.get("status") and resp.get("data"):
            return resp["data"] or []
        return []
    except Exception as exc:
        log.error("get_order_book failed: %s", exc)
        return []
