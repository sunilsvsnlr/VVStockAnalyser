"""
scheduler.py — Automated VVV daily job runner.

Scheduled jobs (IST timezone):
  09:45 AM — Morning check: regime status + EXIT/WARNING position alerts
  03:35 PM — EOD scan: full regime + breakout scanner + position summary

Usage:
  python scheduler.py           # start background scheduler (runs until interrupted)
  python scheduler.py --once    # run EOD job immediately and exit
"""

import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from src.alerts import alert_morning_check, run_eod_alerts
from src.position_tracker import check_positions, load_positions
from src.regime import get_regime
from src.scanner import run_scanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scheduler")

IST = ZoneInfo("Asia/Kolkata")


# ── Job functions ──────────────────────────────────────────────────────────────

def morning_job() -> None:
    """9:45 AM IST — regime + EXIT/WARNING position alerts."""
    log.info("=== Morning Check ===")
    try:
        regime_data  = get_regime()
        positions_df = check_positions(load_positions())
        alert_morning_check(regime_data, positions_df)
        log.info(
            "Morning check done. Regime: %s | Positions: %d",
            regime_data.get("regime"),
            len(positions_df),
        )
    except Exception as exc:
        log.error("Morning job failed: %s", exc, exc_info=True)


def eod_job() -> None:
    """3:35 PM IST — full EOD scan + Telegram summary."""
    log.info("=== EOD Scan ===")
    try:
        regime_data  = get_regime()
        scanner_df   = run_scanner()
        positions_df = check_positions(load_positions())

        log.info(
            "EOD scan done. Regime: %s | Scanner hits: %d | Positions: %d",
            regime_data.get("regime"),
            len(scanner_df),
            len(positions_df),
        )

        run_eod_alerts(regime_data, scanner_df, positions_df)
    except Exception as exc:
        log.error("EOD job failed: %s", exc, exc_info=True)


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="VVV NSE Swing Trading Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the EOD job immediately and exit (useful for testing)",
    )
    parser.add_argument(
        "--morning",
        action="store_true",
        help="Run the morning check immediately and exit",
    )
    args = parser.parse_args()

    if args.once:
        log.info("Running EOD job immediately (--once mode)...")
        eod_job()
        sys.exit(0)

    if args.morning:
        log.info("Running morning check immediately (--morning mode)...")
        morning_job()
        sys.exit(0)

    # ── Scheduled mode ─────────────────────────────────────────────────────────
    scheduler = BlockingScheduler(timezone=IST)

    scheduler.add_job(
        morning_job,
        trigger="cron",
        hour=9,
        minute=45,
        id="morning_check",
        name="Morning regime + position check",
        misfire_grace_time=300,   # allow up to 5 min late
    )

    scheduler.add_job(
        eod_job,
        trigger="cron",
        hour=15,
        minute=35,
        id="eod_scan",
        name="EOD breakout scanner + full summary",
        misfire_grace_time=300,
    )

    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    log.info("Scheduler started at %s", now_ist)
    log.info("Jobs: morning_check @ 09:45 IST | eod_scan @ 15:35 IST")
    log.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
