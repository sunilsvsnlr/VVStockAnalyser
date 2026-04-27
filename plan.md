# VVV Momentum / Breakout Trading System

**Clear & Actionable Trading Plan**  
Based on @VVVStockAnalyst (Volatility Volume and Value)  
IIT Madras alumnus | 8-figure momentum/breakout trader | Building @ValvoIntel  

**Important Disclaimer**  
This document is an educational reconstruction from his public tweets and marked charts (especially the April 2026 "Final Showdown" batch).  
@VVVStockAnalyst is **not SEBI registered**. All content is shared for learning purposes only.  
Past results (e.g., MTAR +43%, Hitachi +22%, BSE +18%) do not guarantee future performance.  
Trading carries substantial risk of capital loss. Always test thoroughly with small position sizes.

---

## 1. Core Philosophy

- **Trading Style**: Momentum and breakout swing trading (holding period: few days to a few weeks).
- **Three Pillars (VVV)**: Volatility (clean momentum moves), Volume (strong confirmation), Value (liquidity + leadership potential).
- **Risk Mantra**: Cut losers quickly. Let winners run.
- **Goal**: Achieve asymmetric returns — small losses (2–3%) offset by large winners (10–43%+).
- **Portfolio Approach**: Concentrated (maximum 4–7 positions).
- **Mindset**: Start conservatively ("Gear 1"). Use early profits as a mental cushion. Reduce size when traveling or distracted.

---

## 2. Market Regime Filter (Highest Priority Rule)

**Only trade aggressively in strong market conditions.**

### Green Regime (New Entries Allowed)
- Major indices (Nifty, Smallcap 100, Midcap 150) trading comfortably **above** 5DMA and 20DMA.
- Leaders showing sustained follow-through.
- Broad participation with many stocks holding above their 5DMA.

### Red / Pause Regime
- Indices or multiple leaders closing **below** 5DMA.
- Recent breakouts appearing weak, "squatting", or failing.
- Signs of vicious rotation or stretched market.

**Action in Pause Regime**: Stop new entries. Only trail existing positions. Consider exiting fully if you have low availability.

**Daily Check**: Monitor percentage of leaders above 5DMA and quality of recent breakouts.

---

## 3. Stock Universe & Pre-Filters

- **Exchange**: NSE (focus on liquid stocks only).
- **Market Cap**: Mid-cap and small-cap with good liquidity. Avoid micro-caps and illiquid names.
- **Liquidity Requirement**: Average daily volume > 5–10 lakh shares (or daily value > ₹10–20 Cr).
- **Preference**: Leading stocks in leading sectors with signs of institutional interest.
- **Exclude**: Penny stocks, extremely volatile erratic movers, and low-quality names.

---

## 4. Daily Scanner Criteria

### Technical Conditions
- Price near or breaking out from a consolidation/base (ideally within 20–25% of 52-week high).
- Strong volume surge: Today's volume ≥ 1.5–2× 20-day average volume.
- Price showing strength by pushing through resistance and sustaining till EOD.
- Stock trading smoothly **above** 5DMA in continuation setups.
- Good relative strength versus Nifty or its sector.

### Qualitative Edge (Observed in Practice)
- "Leading stock. Leading sector. Liquid Leader." (e.g., Hitachi Energy example).
- Clean price action with potential for sustained multi-day moves.

**Example Scanner Logic** (adapt for ChartInk, TradingView, or code):
- Close > 5DMA  
- Volume > 1.5 × SMA(Volume, 20)  
- Close ≥ 75–80% of 52-week high  
- Market Cap > ₹2,000 Cr (adjust for liquidity)

Add a sector-ranking filter: Stock’s recent return > sector average.

---

## 5. Entry Rules

- Prefer **End-of-Day (EOD) confirmation** — stock pushing through resistance and closing strong.
- Trigger: Breakout candle with volume support, or healthy pullback to 5DMA/10DMA in an uptrend.
- Re-entries are allowed when a stock shows renewed strength after an earlier exit.
- Position Sizing: Begin small. Increase size only after consistent performance and with a profit cushion.
- Keep total open positions between 4 and 7.

---

## 6. Exit & Risk Management Rules

### Primary Tool: 5-Day Moving Average (5DMA)
- **Hold** while price sails smoothly **above** the 5DMA.
- **Exit** on a **close below** the 5DMA (applies to both winners and losers).

### Losers
- Cut immediately on 5DMA break or clear weakness.
- Typical loss: –2% to –4% per trade.

### Winners
- Let them run as long as they stay above the 5DMA.
- Trail using the 5DMA.
- Book partial or full profits into strength when momentum slows.

### Full Portfolio Exit Triggers
- Market regime turns negative (indices/leaders break 5DMA + weak breakouts).
- Personal reasons (travel, commitments) — reduce size in advance.

**Real Examples from April 2026 "Final Showdown" (9 trades, 6 winners)**:
- **MTAR**: +43% (monster winner, strong momentum).
- **Hitachi Energy**: +22% ("Leading stock. Leading sector. Liquid Leader." — sailed smoothly above 5DMA for 10+ days).
- **BSE**: +18%.
- **Ather Energy**: Re-added after earlier exit, closed at –3% loss (quick cut).
- **NationalAlum**: Closed on 5DMA break.
- **Avanti Feeds**: Booked –2% loss.

Result: ~3.5–4% positive portfolio impact (17.5 Lacs absolute gains). He closed everything due to upcoming personal commitments and fading breakouts.

---

## 7. Daily Position Management

- Review all open positions against their 5DMA.
- Flag any position approaching or breaking the 5DMA as "Needs Action".
- Track live percentage gains (e.g., MTAR leading at +43%).
- Reduce position sizes when traveling to manage stress effectively.
- Maintain discipline: Focus on regime awareness and quick loss cutting.

---

## 8. Building a ValvoIntel-Style Intelligent Cockpit

Valvo Intelligence is an **AI-powered trading cockpit** featuring:
- Institutional-grade scoring
- Real-time position tracking
- AI-driven insights ("Needs Action" vs. "Healthy Positions")
- Early alerts based on your personal trading rules

### Suggested Features for Your Own Version
- **Market Regime Dashboard**: Green/Yellow/Red status based on 5DMA across indices and leaders.
- **Scanner Output**: Daily list with "Monster Winner Potential" score.
- **Position Manager**: Auto alerts for 5DMA breaks + intelligent hold/exit suggestions.
- **Scoring Components**: Technical strength, momentum, liquidity, and sector leadership.
- **Tech Ideas**: Use NSE data feeds, pandas_ta for indicators, Streamlit for UI, and Telegram for alerts.

---

## 9. Implementation Roadmap

1. **Week 1**: Build and test a basic scanner in ChartInk or TradingView.
2. **Week 2**: Add 5DMA trailing logic and backtest on recent winners (MTAR, Hitachi, BSE style setups).
3. **Week 3**: Create a simple regime dashboard and position tracker (Excel/Google Sheets or basic app).
4. **Weeks 4–8**: Paper trade the full system. Prioritize discipline over perfect entries.
5. **Advanced**: Develop a mini cockpit with automated alerts and scoring.

---

## 10. Key Takeaways from VVV’s Execution

- Market regime awareness prevents over-trading in weak conditions.
- Strict 5DMA trailing creates natural asymmetry.
- Liquidity and sector leadership improve odds of sustained moves.
- Personal availability directly influences position sizing and exits.
- Sharing marked charts helps learning — focus on process, not copying trades.

**Final Reminder**  
This system showed strong results in a short trending phase through disciplined execution. Replicate only after thorough testing and with risk capital you can afford to lose.

---

**Document Version**: Revised April 2026  
**Source**: Public posts and charts from @VVVStockAnalyst  
For latest updates, follow @VVVStockAnalyst and @ValvoIntel on X.

---

## 11. Verified Trade Data — April 2026 "Final Showdown"

Data reconstructed from @VVVStockAnalyst screenshots (Valvo Intelligence dashboard).

### All 9 Trades

| # | Stock | Entry Date | Entry ₹ | Qty | Invested | Exit Date | P&L | Result |
|---|-------|-----------|---------|-----|----------|-----------|-----|--------|
| 1 | MTAR Technologies | Apr 08 | ₹3,776.34 | 420 | ₹15.86L | Apr 23 | +43.0% | WIN |
| 2 | Hitachi Energy | Apr 08 | ₹25,820.00 | 100 | ₹25.82L | Apr 23 | +21.6% | WIN |
| 3 | BSE Ltd | Apr 08 | ₹2,930.65 | 870 | ₹25.50L | Apr 23 | +18.0% | WIN |
| 4 | Ather Energy #2 | Apr 22 (re-entry) | — | — | — | Apr 23 | +4.4% | WIN |
| 5 | NALCO | Apr 08 | ₹410.83 | 7,400 | ₹30.40L | Apr 21 | +3.2% | WIN |
| 6 | MCX | Apr 08 | ₹2,752.00 | 600 | ₹16.51L | Apr 23 | +1.6% | WIN |
| 7 | Ather Energy #1 | Apr 08 | ₹814.49 | 1,900 | ₹15.48L | ~Apr 18 | -3.1% | LOSS |
| 8 | Avanti Feeds | Apr 16–20 | ₹1,508.46 | 1,330 | ₹20.06L | Apr 21 | -2.3% | LOSS |
| 9 | Gallantt Ispat | Apr 16–20 | — | — | — | ~Apr 18 | -2.7% | LOSS |

**Total deployed (6 core positions, Apr 8):** ₹1,29,56,593  
**Portfolio impact:** +3.5% · **Absolute gains:** ₹17.5 Lacs  
**Win/Loss ratio:** 5.7× (avg win +15.3% vs avg loss -2.7%)

### Key Observations

- All 6 core positions entered on a **single day (Apr 8)** — regime confirmation was the trigger, not a daily scan.
- MTAR captured 71% of its final 43% gain in the first 7 days (Apr 8–15).
- Avanti Feeds (entered Apr 16–20, day 12–16 of rally) failed — breadth was already stretched.
- NALCO closed on **5DMA close Apr 21** — textbook plan §6 exit.
- Ather Energy traded **twice** — quick -3.1% cut on 5DMA break, re-entered Apr 22 for +4.4%.

### Plan Alignment Verdict

Every trade decision maps directly to a rule in this document:

| Rule (plan.md §) | VVV Execution | Aligned |
|---|---|---|
| §2 Regime filter before entry | Entered day 5 of GREEN rally | ✅ |
| §6 5DMA trailing stop | Used for all 7 exits | ✅ |
| §6 Cut losers 2–4% | Ather -3.1%, Avanti -2.3%, Gallantt -2.7% | ✅ |
| §6 Let winners run | MTAR held 15 days → +43% | ✅ |
| §5 4–7 concentrated positions | Max 6 open at any time | ✅ |
| §3 Leading stock, leading sector | Hitachi, MTAR, BSE = sector leaders | ✅ |
| §5 EOD confirmation entry | Bulk Apr 8 entry post regime confirm | ✅ |
| §7 Reduce size when travelling | Explicitly done Apr 22 | ✅ |
| §5 Re-entries on renewed strength | Ather #2 re-entered Apr 22 | ✅ |
| §2 No new entries in stretched market | Stopped after Apr 21 breadth warning | ✅ |

**One gap vs this plan's scanner approach:** VVV uses a pre-curated watchlist of 10–15 leaders, not a daily 80-stock scan. The regime turning GREEN triggers bulk deployment of the watchlist — the scanner is for discovery only.

---

## 12. System Implementation

This repository contains a fully automated trading cockpit built from the above strategy.

### Architecture

```
yfinance (historical) ──┐
                        ├── src/data_fetcher.py
Angel One API (live) ───┘
        │
        ├── src/indicators.py   (5DMA, 20DMA, RSI, vol ratio)
        ├── src/regime.py       (GREEN / YELLOW / RED)
        ├── src/scanner.py      (0–10 VVV breakout score)
        └── src/position_tracker.py  (HEALTHY / WARNING / EXIT)
                │
                ├── src/alerts.py    (Telegram notifications)
                ├── app.py           (Streamlit dashboard)
                └── scheduler.py     (9:45 AM + 3:35 PM IST)
```

### Files

| File | Description |
|---|---|
| `src/config.py` | Index tickers, scanner thresholds, 60-stock NSE universe |
| `src/data_fetcher.py` | yfinance historical + Angel One live quotes with fallback |
| `src/indicators.py` | 5DMA, 20DMA, volume ratio, RSI14, 52W high via pandas_ta |
| `src/regime.py` | GREEN/YELLOW/RED filter — Nifty50, Smallcap100, Midcap150 |
| `src/scanner.py` | EOD breakout scanner with 10-point VVV scoring model |
| `src/position_tracker.py` | 5DMA trailing stop — HEALTHY/WARNING/EXIT status |
| `src/alerts.py` | Telegram bot: regime, scanner top-10, position alerts |
| `app.py` | Streamlit dashboard — 4 sections |
| `scheduler.py` | APScheduler jobs — morning check + EOD scan |
| `fetch_vvv_tweets.mjs` | Node.js script to fetch @VVVStockAnalyst tweets via Rettiwt-API |
| `positions.json` | Open positions store |
| `requirements.txt` | Python dependencies |
| `package.json` | Node.js dependencies |

### Breakout Scoring (0–10)

Each criterion awards 1 point:

1. Close > 5DMA
2. Close > 20DMA
3. Volume ≥ 1.5× 20-day average
4. Volume ≥ 2.0× 20-day average *(bonus)*
5. Price ≥ 75% of 52-week high
6. Price ≥ 85% of 52-week high *(bonus)*
7. RSI14 > 55
8. RSI14 > 65 *(bonus)*
9. 1-day return > 1%
10. 5-day return > 3%

Signal labels: **MONSTER** (9–10) · **STRONG** (7–8) · **WATCH** (5–6)

### Dashboard Sections

- **A. Market Regime** — colour-coded GREEN/YELLOW/RED banner with per-index 5DMA/20DMA cards
- **B. Breakout Scanner** — run on demand, sortable table, CSV download
- **C. Position Tracker** — add/remove positions via sidebar, live P&L, 5DMA status
- **D. Telegram Alerts** — send EOD summary, morning check, or regime-only

### Scheduler Jobs (IST)

| Time | Job |
|---|---|
| 09:45 AM | Regime status + EXIT/WARNING position alerts |
| 03:35 PM | Full EOD scan + scanner results + position summary |

See `README.md` for full setup and run instructions.
