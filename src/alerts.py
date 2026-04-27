"""
alerts.py — Telegram notification layer for the VVV trading system.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from config (loaded via .env).
All public functions are fire-and-forget: they log failures but don't raise.
"""

import logging

import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


# ── Core send ──────────────────────────────────────────────────────────────────

def _send_telegram(message: str, parse_mode: str = "Markdown") -> bool:
    """
    POST a message to the configured Telegram chat.
    Returns True on success, False on any failure.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return False

    url = _TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": parse_mode,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200 and resp.json().get("ok"):
            log.debug("Telegram message sent (%d chars)", len(message))
            return True
        log.warning("Telegram API error: %s", resp.text[:200])
        return False
    except requests.RequestException as exc:
        log.error("Telegram send failed: %s", exc)
        return False


# ── Formatted alert builders ───────────────────────────────────────────────────

def alert_regime(regime_data: dict) -> bool:
    """Send market regime status to Telegram."""
    regime  = regime_data.get("regime", "UNKNOWN")
    emoji   = regime_data.get("regime_emoji", "")
    detail  = regime_data.get("detail", "")
    indices = regime_data.get("indices", {})

    lines = [f"{emoji} *MARKET REGIME: {regime}*", detail, ""]

    for name, info in indices.items():
        status = info.get("status", "")
        close  = info.get("close", "—")
        dma5   = info.get("dma5", "—")
        pct    = info.get("pct_vs_5dma", 0)
        tick   = "✅" if "ABOVE" in status else "❌"
        lines.append(f"{tick} *{name}*: {close} | 5DMA {dma5} ({pct:+.1f}%)")

    return _send_telegram("\n".join(lines))


def alert_scanner(scanner_df, top_n: int = 10) -> bool:
    """Send top scanner hits to Telegram."""
    if scanner_df is None or scanner_df.empty:
        return _send_telegram("📊 *SCANNER*: No breakout candidates today.")

    top = scanner_df.head(top_n)
    lines = [f"📊 *TOP BREAKOUT CANDIDATES* ({len(scanner_df)} total)\n"]

    for _, row in top.iterrows():
        signal = row.get("signal", "")
        sym    = row.get("symbol", "")
        score  = row.get("score", 0)
        vol    = row.get("vol_ratio", 0)
        rsi    = row.get("rsi14", 0)
        h52    = row.get("pct_52w_high", "")
        r1d    = row.get("ret_1d", "")

        star = "⭐" if signal == "MONSTER" else ("🔥" if signal == "STRONG" else "👁")
        lines.append(
            f"{star} *{sym}* — {score}/10 | Vol {vol:.1f}× | RSI {rsi:.0f} | "
            f"52W {h52} | 1D {r1d}"
        )

    return _send_telegram("\n".join(lines))


def alert_positions(positions_df) -> bool:
    """Send EXIT and WARNING position alerts to Telegram."""
    if positions_df is None or positions_df.empty:
        return _send_telegram("📋 *POSITIONS*: No open positions tracked.")

    lines = ["⚠️ *POSITION TRACKER*\n"]

    for _, row in positions_df.iterrows():
        status = row.get("status", "UNKNOWN")
        sym    = row.get("symbol", "")
        gap    = row.get("gap_to_5dma_pct")
        pnl    = row.get("pnl_pct", 0)
        price  = row.get("current_price", 0)
        dma5   = row.get("dma5", "—")

        if status == "EXIT":
            icon = "🔴"
        elif status == "WARNING":
            icon = "🟡"
        else:
            icon = "🟢"

        gap_str = f"{gap:+.1f}%" if gap is not None else "—"
        lines.append(
            f"{icon} *{sym}* [{status}] ₹{price} | 5DMA ₹{dma5} ({gap_str}) | P&L {pnl:+.1f}%"
        )

    return _send_telegram("\n".join(lines))


def run_eod_alerts(regime_data: dict, scanner_df, positions_df) -> None:
    """
    Compose and dispatch the full EOD summary as three Telegram messages:
    1. Regime status
    2. Scanner results
    3. Position alerts
    """
    log.info("Sending EOD Telegram alerts...")
    alert_regime(regime_data)
    alert_scanner(scanner_df, top_n=10)
    alert_positions(positions_df)
    log.info("EOD alerts sent.")


def alert_morning_check(regime_data: dict, positions_df) -> None:
    """
    Morning check at 9:45 AM IST:
    1. Regime status
    2. Any EXIT-status positions (urgent action needed)
    """
    log.info("Sending morning check alerts...")
    alert_regime(regime_data)

    if positions_df is not None and not positions_df.empty:
        exits = positions_df[positions_df["status"] == "EXIT"]
        warnings = positions_df[positions_df["status"] == "WARNING"]
        if not exits.empty or not warnings.empty:
            alert_positions(positions_df)
        else:
            _send_telegram("✅ *Morning Check*: All positions healthy above 5DMA.")
    log.info("Morning alerts sent.")
