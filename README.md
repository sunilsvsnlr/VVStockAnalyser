# VVV NSE Swing Trading Dashboard

An automated trading cockpit for NSE equity swing trading, built on the **@VVVStockAnalyst (Volatility Volume Value)** methodology.

Features:
- **Market Regime Filter** — GREEN / YELLOW / RED across Nifty50, Smallcap100, Midcap150
- **Breakout Scanner** — 10-point VVV scoring (5DMA + volume surge + 52W proximity + RSI)
- **Position Tracker** — 5DMA trailing stop with HEALTHY / WARNING / EXIT alerts
- **Telegram Notifications** — EOD summary, morning check, regime alerts
- **Streamlit Dashboard** — live UI with 4 sections
- **Automated Scheduler** — 9:45 AM + 3:35 PM IST daily jobs
- **Twitter Fetcher** — pull @VVVStockAnalyst trade tweets via Rettiwt-API

> **Disclaimer**: Educational reconstruction of a public trading methodology. Not SEBI registered. Not financial advice. Always test with small position sizes.

---

## Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core system |
| Node.js | 22+ | Twitter fetcher |
| npm | 9+ | Node packages |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sunilsvsnlr/VVStockAnalyser.git
cd VVStockAnalyser
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node.js dependencies

```bash
npm install
```

### 4. Create your `.env` file

```bash
cp .env.example .env   # or create manually
```

Edit `.env` with your credentials:

```env
# Angel One SmartAPI (for live quotes during market hours)
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_ID=your_client_id
ANGEL_TOTP_SECRET=your_totp_secret
ANGEL_MPIN=your_mpin

# Telegram Bot (for alerts)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Twitter / X (for tweet fetcher — optional)
RETTIWT_API_KEY=your_rettiwt_key
```

#### Getting each credential

**Angel One API key:**
1. Log into [smartapi.angelbroking.com](https://smartapi.angelbroking.com)
2. Create an app → copy `API Key`
3. Enable TOTP in My Profile → copy the TOTP secret

**Telegram Bot:**
1. Message `@BotFather` on Telegram → `/newbot`
2. Copy the `BOT_TOKEN`
3. Get your `CHAT_ID`: message `@userinfobot` or use `@getidsbot`

**Rettiwt API key (Twitter fetcher):**
1. Install the browser extension:
   - Chrome: [X Auth Helper](https://chromewebstore.google.com/detail/x-auth-helper/igpkhkjmpdecacocghpgkghdcmcmpfhp)
   - Firefox: [Rettiwt Auth Helper](https://addons.mozilla.org/en-US/firefox/addon/rettiwt-auth-helper)
2. Open incognito → go to `x.com` → log in
3. Click extension → **Get Key** → copy it into `.env`

---

## Running the System

### Streamlit Dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

**Dashboard sections:**

| Section | What it does |
|---|---|
| A. Market Regime | GREEN/YELLOW/RED banner + per-index 5DMA/20DMA cards |
| B. Breakout Scanner | Click "Run Scanner" → scored breakout candidates table + CSV download |
| C. Position Tracker | Add positions via sidebar → live P&L + 5DMA status |
| D. Telegram Alerts | Send EOD summary / morning check / regime-only to Telegram |

### Automated Scheduler

```bash
# Run continuously (fires at 9:45 AM and 3:35 PM IST every weekday)
python scheduler.py

# Run the EOD job immediately (for testing)
python scheduler.py --once

# Run the morning check immediately
python scheduler.py --morning
```

### Twitter Fetcher

```bash
# Fetch last 3 pages of @VVVStockAnalyst tweets, filter for 8 stocks
node fetch_vvv_tweets.mjs

# Fetch more history
node fetch_vvv_tweets.mjs --pages 10

# Print all tweets (no stock filter)
node fetch_vvv_tweets.mjs --all
```

> Requires `RETTIWT_API_KEY` in `.env`. See Setup above.

---

## Testing Each Component

### 1. Market Regime

```bash
python3 -c "
from src.regime import get_regime
import json
r = get_regime()
print('Regime:', r['regime'])
print('Detail:', r['detail'])
for name, info in r['indices'].items():
    print(f'  {name}: close={info[\"close\"]} 5DMA={info[\"dma5\"]} status={info[\"status\"]}')
"
```

Expected output:
```
Regime: GREEN
Detail: All indices above 5DMA & 20DMA — new entries allowed
  NIFTY50: close=24500.0 5DMA=24100.0 status=ABOVE_BOTH
  ...
```

### 2. Breakout Scanner

```bash
python3 -c "
from src.scanner import run_scanner
df = run_scanner()
print(df.head(10).to_string())
print(f'\nTotal candidates: {len(df)}')
"
```

Expected output — a table of NSE stocks scored 5–10, sorted by score descending.

### 3. Position Tracker

Add a test position then check it:

```bash
python3 -c "
from src.position_tracker import add_position, check_positions, load_positions, remove_position

# Add a test position
add_position('MTARTECH', 3776.34, 10, '2026-04-08', 'Test position')

# Check it
df = check_positions(load_positions())
print(df.to_string())

# Clean up
remove_position('MTARTECH')
print('Test position removed.')
"
```

Expected output — table showing current price, 5DMA, P&L%, and status (HEALTHY/WARNING/EXIT).

### 4. Telegram Alerts

```bash
python3 -c "
from src.alerts import _send_telegram
ok = _send_telegram('Test from VVV Dashboard — setup working!')
print('Sent:', ok)
"
```

Check your Telegram chat for the message.

### 5. Data Fetcher

```bash
python3 -c "
from src.data_fetcher import get_historical
data = get_historical(['MTARTECH.NS', 'BSE.NS'], period='5d')
for sym, df in data.items():
    print(f'{sym}: {len(df)} rows, latest close = {df[\"Close\"].iloc[-1]:.2f}')
"
```

### 6. Indicators

```bash
python3 -c "
from src.data_fetcher import get_historical
from src.indicators import add_indicators, pct_above_5dma
df = get_historical(['MTARTECH.NS'], period='30d')['MTARTECH.NS']
df = add_indicators(df)
print(df[['Close','dma5','dma20','vol_ratio','rsi14']].tail(5).to_string())
print(f'Gap to 5DMA: {pct_above_5dma(df):+.2f}%')
"
```

### 7. Full EOD Run (dry test)

```bash
python scheduler.py --once
```

This runs the complete EOD pipeline — regime check, scanner, position check — and sends results to Telegram.

---

## Project Structure

```
VVStockAnalyser/
├── app.py                    # Streamlit dashboard (4-section UI)
├── scheduler.py              # APScheduler — 9:45 AM + 3:35 PM IST
├── fetch_vvv_tweets.mjs      # Rettiwt-API Twitter fetcher (Node.js)
├── positions.json            # Open positions store (edit via dashboard)
├── requirements.txt          # Python dependencies
├── package.json              # Node.js dependencies
├── plan.md                   # VVV strategy + verified trade data + implementation notes
├── .env                      # Credentials (git-ignored)
├── references/
│   └── angel_api.py          # Angel One SmartAPI integration (source)
└── src/
    ├── config.py             # Constants, universe, thresholds
    ├── data_fetcher.py       # yfinance + Angel One data layer
    ├── indicators.py         # 5DMA, 20DMA, RSI, vol ratio (pandas_ta)
    ├── regime.py             # GREEN/YELLOW/RED market regime
    ├── scanner.py            # Breakout scanner with VVV scoring
    ├── position_tracker.py   # 5DMA trailing stop tracker
    └── alerts.py             # Telegram notification layer
```

---

## Customisation

### Change the equity universe

Edit `src/config.py` → `EQUITY_UNIVERSE` list. Add/remove NSE symbols with `.NS` suffix.

### Adjust scanner thresholds

Edit `src/config.py`:

```python
VOL_SURGE_THRESHOLD = 1.5   # minimum volume surge ratio
HIGH_52W_PCT        = 0.75  # minimum % of 52-week high
SCORE_MIN_FILTER    = 5     # minimum score to appear in results
```

### Change scheduler times

Edit `scheduler.py` → `morning_job` and `eod_job` cron triggers:

```python
scheduler.add_job(morning_job, trigger="cron", hour=9, minute=45, ...)
scheduler.add_job(eod_job,     trigger="cron", hour=15, minute=35, ...)
```

### Add a curated watchlist

The April 2026 analysis showed VVV pre-selects 10–15 leaders before regime confirmation, then deploys in bulk when regime turns GREEN. To replicate:

1. Add `watchlist.json` with your pre-vetted stocks
2. When regime = GREEN, the dashboard's Position Tracker sidebar shows "Ready to deploy" stocks

---

## Dependencies

### Python (`requirements.txt`)

| Package | Purpose |
|---|---|
| `streamlit` | Dashboard UI |
| `yfinance` | Historical OHLCV data |
| `pandas_ta` | Technical indicators |
| `pandas` | Data processing |
| `requests` | Telegram API calls |
| `apscheduler` | Scheduled jobs |
| `SmartApi-python` | Angel One live quotes |
| `pyotp` | TOTP for Angel One login |
| `python-dotenv` | Load `.env` credentials |

### Node.js (`package.json`)

| Package | Purpose |
|---|---|
| `rettiwt-api` | Twitter/X timeline fetcher (no official API needed) |

---

## Known Limitations

- **yfinance / Angel One**: Both require internet access. Angel One live quotes only work during NSE market hours (Mon–Fri, 9:15–15:30 IST).
- **Rettiwt guest auth**: X/Twitter blocked unauthenticated access in 2024. A real account API key is required (generated via browser extension — see Setup).
- **pandas_ta**: Requires Python 3.11 or below (not compatible with 3.12+). Use `pip install pandas_ta` on Python ≤ 3.11.
- **Regime index tickers**: `^CNXMD` (Midcap150) may not be available on all yfinance versions. Fallback: use `NIFTY_MID_SELECT.NS`.

---

## Disclaimer

This project is an educational tool built from publicly available information shared by @VVVStockAnalyst on X. It is not a SEBI-registered service. All trade examples are for learning purposes only. Past performance does not guarantee future results. Always test with small position sizes and consult a SEBI-registered advisor before investing.
