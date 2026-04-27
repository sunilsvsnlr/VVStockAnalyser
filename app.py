"""
app.py — VVV NSE Swing Trading Dashboard (Streamlit).

Sections:
  A. Market Regime     — GREEN / YELLOW / RED banner + per-index cards
  B. Breakout Scanner  — EOD scan results table, download CSV
  C. Position Tracker  — Open positions with P&L and 5DMA status
  D. Alerts            — Send Telegram + in-app alert log
"""

import json
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from src.alerts import alert_morning_check, alert_regime, run_eod_alerts
from src.config import EQUITY_UNIVERSE
from src.position_tracker import (
    add_position,
    check_positions,
    load_positions,
    remove_position,
)
from src.regime import get_regime
from src.scanner import run_scanner

logging.basicConfig(level=logging.INFO)

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VVV Swing Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ─────────────────────────────────────────────────────────

if "alert_log" not in st.session_state:
    st.session_state.alert_log = []

if "scanner_df" not in st.session_state:
    st.session_state.scanner_df = None

if "scanner_ts" not in st.session_state:
    st.session_state.scanner_ts = None


# ── Cached data loaders ────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def cached_regime() -> dict:
    return get_regime()


@st.cache_data(ttl=300, show_spinner=False)
def cached_positions() -> pd.DataFrame:
    return check_positions(load_positions())


# ── Helpers ────────────────────────────────────────────────────────────────────

def _regime_badge(regime: str, color: str) -> None:
    st.markdown(
        f"""<div style="background:{color};padding:10px 20px;border-radius:8px;
        display:inline-block;color:#fff;font-size:1.4rem;font-weight:700;
        letter-spacing:1px;">{regime}</div>""",
        unsafe_allow_html=True,
    )


def _color_status(val: str) -> str:
    return {
        "EXIT":    "background-color:#e74c3c;color:#fff;font-weight:bold",
        "WARNING": "background-color:#f39c12;color:#fff;font-weight:bold",
        "HEALTHY": "background-color:#2ecc71;color:#fff;font-weight:bold",
    }.get(val, "")


def _color_score(val: int) -> str:
    if val >= 9:
        return "background-color:#27ae60;color:#fff;font-weight:bold"
    if val >= 7:
        return "background-color:#2980b9;color:#fff;font-weight:bold"
    if val >= 5:
        return "background-color:#8e44ad;color:#fff"
    return ""


def _color_pnl(val: float) -> str:
    if val > 0:
        return "color:#27ae60;font-weight:bold"
    if val < 0:
        return "color:#e74c3c;font-weight:bold"
    return ""


def _log_alert(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.alert_log.insert(0, f"[{ts}] {msg}")
    st.session_state.alert_log = st.session_state.alert_log[:20]


# ── Sidebar — position management ──────────────────────────────────────────────

with st.sidebar:
    st.title("📈 VVV Swing Trader")
    st.caption("Based on @VVVStockAnalyst methodology")
    st.divider()

    st.subheader("Add Position")
    with st.form("add_pos_form", clear_on_submit=True):
        sym_input    = st.text_input("Symbol (e.g. MTARTECH)", placeholder="MTARTECH")
        entry_price  = st.number_input("Entry Price (₹)", min_value=0.01, value=100.0, step=0.5)
        qty_input    = st.number_input("Quantity", min_value=1, value=10, step=1)
        entry_date   = st.date_input("Entry Date")
        notes_input  = st.text_input("Notes (optional)", placeholder="Breakout with volume")
        submitted    = st.form_submit_button("Add Position")

    if submitted and sym_input.strip():
        add_position(
            sym_input.strip(),
            float(entry_price),
            int(qty_input),
            str(entry_date),
            notes_input.strip(),
        )
        cached_positions.clear()
        _log_alert(f"Added position: {sym_input.upper()}")
        st.rerun()

    st.divider()

    st.subheader("Remove Position")
    positions_list = load_positions()
    if positions_list:
        sym_to_remove = st.selectbox(
            "Select symbol to remove",
            options=[p["symbol"].replace(".NS", "") for p in positions_list],
        )
        if st.button("Remove", type="secondary"):
            remove_position(sym_to_remove)
            cached_positions.clear()
            _log_alert(f"Removed position: {sym_to_remove}")
            st.rerun()
    else:
        st.caption("No open positions.")

    st.divider()
    if st.button("Clear All Caches"):
        cached_regime.clear()
        cached_positions.clear()
        st.session_state.scanner_df = None
        st.rerun()


# ── Main layout ────────────────────────────────────────────────────────────────

st.title("VVV NSE Swing Trading Dashboard")
st.caption(
    "Strategy: Momentum & breakout swing trading | 5DMA trailing stop | "
    "Market regime filter | Based on @VVVStockAnalyst"
)

# ═══════════════════════════════════════════════════════════════
# SECTION A — Market Regime
# ═══════════════════════════════════════════════════════════════

st.header("A. Market Regime")

with st.spinner("Fetching index data..."):
    regime_data = cached_regime()

regime       = regime_data.get("regime", "UNKNOWN")
regime_color = regime_data.get("regime_color", "#999")
regime_emoji = regime_data.get("regime_emoji", "")
detail       = regime_data.get("detail", "")
indices      = regime_data.get("indices", {})

col_badge, col_detail = st.columns([1, 3])
with col_badge:
    _regime_badge(f"{regime_emoji} {regime}", regime_color)
with col_detail:
    st.markdown(f"**{detail}**")
    st.caption(
        "GREEN = new entries allowed | YELLOW = reduce size | RED = no new entries"
    )

st.divider()

# Per-index cards
idx_cols = st.columns(len(indices))
for col, (name, info) in zip(idx_cols, indices.items()):
    with col:
        status = info.get("status", "NO_DATA")
        close  = info.get("close", "—")
        dma5   = info.get("dma5", "—")
        dma20  = info.get("dma20", "—")
        pct    = info.get("pct_vs_5dma", 0)

        border_color = (
            "#2ecc71" if "ABOVE_BOTH" in status
            else "#f39c12" if "ABOVE_5" in status
            else "#e74c3c"
        )
        icon = "✅" if "ABOVE_BOTH" in status else ("⚠️" if "ABOVE_5" in status else "❌")
        st.markdown(
            f"""<div style="border:2px solid {border_color};border-radius:8px;
            padding:12px;text-align:center;">
            <div style="font-size:1.1rem;font-weight:700">{icon} {name}</div>
            <div style="font-size:1.4rem;font-weight:bold">₹{close:,}</div>
            <div style="font-size:0.85rem;color:#888">5DMA: ₹{dma5:,}
            <span style="color:{border_color}">{pct:+.1f}%</span></div>
            <div style="font-size:0.8rem;color:#888">20DMA: ₹{dma20:,}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════
# SECTION B — Breakout Scanner
# ═══════════════════════════════════════════════════════════════

st.header("B. Breakout Scanner (5DMA + Volume Surge)")

if regime == "RED":
    st.warning(
        "Market regime is RED — new entries not recommended per VVV rules. "
        "Scanner results shown for informational purposes only."
    )
elif regime == "YELLOW":
    st.info("Market regime is YELLOW — proceed with caution and reduced size.")

scan_col1, scan_col2, scan_col3 = st.columns([1, 1, 4])

with scan_col1:
    run_scan = st.button("Run Scanner", type="primary")

with scan_col2:
    custom_scan = st.checkbox("Use custom universe")

if run_scan:
    with st.spinner(f"Scanning {len(EQUITY_UNIVERSE)} stocks..."):
        universe = None
        if custom_scan:
            custom_text = st.text_area(
                "Enter symbols (one per line, no .NS needed)",
                height=100,
                placeholder="MTARTECH\nHITACHIENERGY\nBSE",
            )
            if custom_text.strip():
                universe = [
                    s.strip().upper() + ".NS"
                    for s in custom_text.splitlines()
                    if s.strip()
                ]
        st.session_state.scanner_df = run_scanner(universe)
        st.session_state.scanner_ts = datetime.now().strftime("%d-%b-%Y %H:%M:%S")

scanner_df = st.session_state.scanner_df
scanner_ts = st.session_state.scanner_ts

if scanner_df is not None:
    if scanner_ts:
        st.caption(f"Last scanned: {scanner_ts}")

    if scanner_df.empty:
        st.info("No breakout candidates found with score ≥ 5 in the current universe.")
    else:
        st.success(f"Found **{len(scanner_df)}** breakout candidates.")

        # Style the dataframe
        def style_scanner(df: pd.DataFrame):
            return df.style.applymap(
                _color_score, subset=["score"]
            ).format({
                "close": "₹{:.2f}",
                "dma5":  "₹{:.2f}",
                "dma20": "₹{:.2f}",
                "vol_ratio": "{:.2f}×",
                "rsi14":     "{:.1f}",
            })

        st.dataframe(
            style_scanner(scanner_df),
            use_container_width=True,
            height=min(400, 55 + len(scanner_df) * 38),
        )

        # Download CSV
        csv_data = scanner_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"scanner_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
else:
    st.info("Click **Run Scanner** to find breakout candidates in the equity universe.")

st.divider()

# ═══════════════════════════════════════════════════════════════
# SECTION C — Position Tracker
# ═══════════════════════════════════════════════════════════════

st.header("C. Position Tracker")

with st.spinner("Loading positions..."):
    positions_df = cached_positions()

if positions_df.empty:
    st.info(
        "No open positions. Use the sidebar to add a position "
        "(e.g. MTARTECH, entry price, quantity)."
    )
else:
    # Summary metrics
    total_pnl   = positions_df["pnl_abs"].sum()
    exits        = (positions_df["status"] == "EXIT").sum()
    warnings     = (positions_df["status"] == "WARNING").sum()
    healthy      = (positions_df["status"] == "HEALTHY").sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Open Positions", len(positions_df))
    m2.metric("Total Unrealised P&L", f"₹{total_pnl:,.0f}",
              delta=f"{total_pnl:+,.0f}")
    m3.metric("EXIT / WARNING", f"{exits} / {warnings}",
              delta=f"{exits} needs action" if exits > 0 else None,
              delta_color="inverse")
    m4.metric("Healthy", healthy)

    if exits > 0:
        st.error(
            f"🔴 {exits} position(s) below 5DMA — exit per VVV rules (plan.md §6)."
        )
    elif warnings > 0:
        st.warning(
            f"🟡 {warnings} position(s) approaching 5DMA — trail tightly."
        )

    # Styled table
    def style_positions(df: pd.DataFrame):
        return df.style.applymap(
            _color_status, subset=["status"]
        ).applymap(
            _color_pnl, subset=["pnl_pct"]
        ).format({
            "entry_price":    "₹{:.2f}",
            "current_price":  "₹{:.2f}",
            "dma5":           "₹{}",
            "gap_to_5dma_pct": "{:+.2f}%",
            "pnl_pct":        "{:+.2f}%",
            "pnl_abs":        "₹{:,.0f}",
        }, na_rep="—")

    display_cols = [
        "symbol", "entry_price", "current_price", "dma5",
        "gap_to_5dma_pct", "pnl_pct", "pnl_abs", "qty",
        "entry_date", "status", "notes",
    ]
    st.dataframe(
        style_positions(positions_df[display_cols]),
        use_container_width=True,
        height=min(400, 55 + len(positions_df) * 38),
    )

    st.caption(
        "EXIT = close below 5DMA (exit now) | "
        "WARNING = within 2% of 5DMA (trail tightly) | "
        "HEALTHY = well above 5DMA (hold)"
    )

    if st.button("Refresh Positions"):
        cached_positions.clear()
        st.rerun()

st.divider()

# ═══════════════════════════════════════════════════════════════
# SECTION D — Telegram Alerts
# ═══════════════════════════════════════════════════════════════

st.header("D. Telegram Alerts")

alert_col1, alert_col2, alert_col3 = st.columns(3)

with alert_col1:
    if st.button("Send Full EOD Summary", type="primary"):
        with st.spinner("Sending EOD alerts via Telegram..."):
            if st.session_state.scanner_df is None:
                st.warning("Run the scanner first to include results in the alert.")
                scan_df_to_send = pd.DataFrame()
            else:
                scan_df_to_send = st.session_state.scanner_df
            pos_df_to_send = cached_positions()
            run_eod_alerts(regime_data, scan_df_to_send, pos_df_to_send)
        _log_alert("EOD summary sent via Telegram")
        st.success("EOD alerts sent to Telegram.")

with alert_col2:
    if st.button("Send Morning Check"):
        with st.spinner("Sending morning check..."):
            alert_morning_check(regime_data, cached_positions())
        _log_alert("Morning check sent via Telegram")
        st.success("Morning check sent.")

with alert_col3:
    if st.button("Send Regime Only"):
        alert_regime(regime_data)
        _log_alert(f"Regime alert sent: {regime}")
        st.success(f"Regime ({regime}) sent to Telegram.")

# Alert log
st.subheader("Alert Log")
if st.session_state.alert_log:
    for entry in st.session_state.alert_log:
        st.text(entry)
else:
    st.caption("No alerts sent this session.")
