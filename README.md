# 8-30 EMA Algo Trader (Zerodha / Kite)

Options algo for NIFTY / BANKNIFTY built on the 8 & 30 EMA crossover strategy with OI, VIX, and news filters.

> **Strategy Guide:** Full strategy explanation, entry rules, filters, and backtesting notes are in [`Algo_Trading_Guide.pdf`](Algo_Trading_Guide.pdf)

---

## Requirements

- Python 3.10+
- Zerodha account with **Kite Connect API** access
- API Key & Secret from [kite.trade/apps](https://kite.trade/apps)

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Open `config.py` and set your credentials and preferences:

```python
API_KEY    = "your_kite_api_key"
API_SECRET = "your_kite_api_secret"
```

> **Tip:** Use environment variables to avoid hardcoding keys:
> ```bash
> export KITE_API_KEY=your_key
> export KITE_API_SECRET=your_secret
> ```

Other settings to review in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `PAPER_TRADING` | `True` | `True` = simulate trades, `False` = real orders |
| `INSTRUMENT` | `"NIFTY"` | `"NIFTY"` or `"BANKNIFTY"` |
| `CAPITAL` | `150000` | Starting capital in Rs. |
| `RISK_PCT` | `0.01` | Risk per trade (1% of capital) |
| `MAX_TRADES_DAY` | `3` | Max trades per day |
| `DAILY_LOSS_LIMIT` | `4500` | Halt trading if loss exceeds this (Rs.) |
| `TIMEFRAME` | `5` | Candle size in minutes |

---

## How to Start — Every Morning

> Do this **before market opens (before 9:15 AM)**

### Step 1 — Zerodha Login

```bash
python3 zerodha_login.py
```

- A browser window will open — login with your Zerodha credentials
- After login, copy the `request_token` from the URL:
  ```
  https://kite.trade/connect/login?request_token=XXXXXXXX&action=login
  ```
- Paste it in the terminal when prompted
- Access token is saved to `logs/access_token.txt` (valid for the day)

### Step 2 — Start the Algo

```bash
python3 algo_trader.py
```

The algo will:
1. Run pre-market checks (VIX, news, OI)
2. Wait until 9:15 AM if market isn't open yet
3. Start scanning candles every 5 minutes
4. Place trades automatically based on signals
5. Print end-of-day report at 3:20 PM

### Step 3 — Start the Dashboard (optional, separate terminal)

```bash
python3 dashboard_server.py
```

Open [http://localhost:4200](http://localhost:4200) to see live P&L, trades, and market data.

---

## Paper Trading vs Real Trading

### Switch to Paper Trading (safe, no real orders)

In `config.py`:

```python
PAPER_TRADING = True
```

All signals and P&L are simulated. No orders are sent to Zerodha.

### Switch to Real Trading (live orders on Zerodha)

In `config.py`:

```python
PAPER_TRADING = False
```

> **Before going live, make sure:**
> - You have tested the strategy in paper mode for at least a few weeks
> - `CAPITAL`, `RISK_PCT`, and `DAILY_LOSS_LIMIT` are set correctly
> - Your Kite API app has **Order** permissions enabled on [kite.trade/apps](https://kite.trade/apps)
> - Sufficient margin is available in your Zerodha account

---

## File Structure

```
├── algo_trader.py        # Main algo — entry point
├── config.py             # All settings (edit this)
├── zerodha_login.py      # Zerodha login helper
├── dashboard_server.py   # Live web dashboard
├── paper_trade.py        # Paper trade engine
├── candle_patterns.py    # Candle pattern logic
├── option_chain.py       # Option price fetching
├── oi_data.py            # Open interest filters
├── iv_filter.py          # VIX filter
├── news_filter.py        # News/event filter
├── report.py             # Trade reporting
├── logs/                 # Trade logs and daily reports
└── templates/            # Dashboard HTML
```

---

## Logs

| File | Description |
|---|---|
| `logs/algo_trade.log` | Master log (all days) |
| `logs/algo_YYYY-MM-DD.log` | Daily log |
| `logs/daily_report.csv` | All trades in CSV |
| `logs/summary_YYYY-MM-DD.json` | Daily summary JSON |
