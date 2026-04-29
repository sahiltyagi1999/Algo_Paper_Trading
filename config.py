"""
Configuration — edit this file before running the algo.
"""
import os

# ── Zerodha Kite API Credentials ──────────────────────────────────────────────
# Loaded from environment variables first, fallback to hardcoded values.
# Best practice: set env vars instead of hardcoding keys.
#   export KITE_API_KEY=your_key
#   export KITE_API_SECRET=your_secret
API_KEY    = os.getenv("KITE_API_KEY",    "7svg0xp2law6wcam")
API_SECRET = os.getenv("KITE_API_SECRET", "7jj0ubfr1q88jqg9odi7ukudf4zdlt3l")

# ── Trading Settings ───────────────────────────────────────────────────────────
PAPER_TRADING    = True          # True = no real orders placed
INSTRUMENT       = "NIFTY"       # "NIFTY" or "BANKNIFTY"
TIMEFRAME        = 5             # candle size in minutes (5 or 15 recommended)
CAPITAL          = 150000        # starting capital in Rs.
RISK_PCT             = 0.01      # risk per trade as fraction of capital (0.01 = 1%)
MAX_CAPITAL_PER_TRADE = 0.30     # max 30% of capital in one trade (prevents overleveraging)
MAX_TRADES_DAY   = 3             # max trades allowed per day
DAILY_LOSS_LIMIT = 4500          # halt trading if day loss exceeds this (Rs.)

# ── EMA Settings ───────────────────────────────────────────────────────────────
EMA_FAST = 8
EMA_SLOW = 30

# ── Candle Pattern Thresholds ──────────────────────────────────────────────────
DOMINANCE_BODY = 0.55            # body/range ratio to qualify as dominance candle
REJECTION_WICK = 0.45            # wick/range ratio to qualify as rejection candle

# ── Signal Filters ─────────────────────────────────────────────────────────────
ADX_THRESHOLD   = 20             # min ADX to confirm trending market
EMA30_PROXIMITY = 0.006          # price must be within 0.6% of EMA30 for retest entry
STRETCH_PCT     = 0.001          # EMA gap > 0.1% of price = stretched (continuation entry)

# ── Entry/Exit Buffers ─────────────────────────────────────────────────────────
SL_BUFFER    = 2.0               # points below/above candle for stop loss
ENTRY_BUFFER = 0.5               # points above/below candle for entry trigger

# ── OI Filter ──────────────────────────────────────────────────────────────────
OI_BUFFER = 50                   # points from OI level to block entry

# ── Market Hours (IST 24h) ─────────────────────────────────────────────────────
MARKET_OPEN    = "09:15"
MARKET_CLOSE   = "15:20"
NO_TRADE_AFTER = "15:00"         # no new entries after this time
OPEN_VOLATILITY_END = "09:45"    # skip first 30 min of market

# ── Notification (optional) ────────────────────────────────────────────────────
# Free WhatsApp alerts via callmebot.com — leave blank to disable
WHATSAPP_PHONE  = ""             # e.g. "+919876543210"
WHATSAPP_APIKEY = ""             # from callmebot.com

# ── File Paths ─────────────────────────────────────────────────────────────────
LOG_FILE    = "logs/algo_trade.log"
REPORT_FILE = "logs/daily_report.csv"
TOKEN_FILE  = "logs/access_token.txt"


# ── Validation ─────────────────────────────────────────────────────────────────
def validate():
    assert 0 < RISK_PCT < 1,          "RISK_PCT must be between 0 and 1"
    assert CAPITAL > 0,               "CAPITAL must be positive"
    assert MAX_TRADES_DAY > 0,        "MAX_TRADES_DAY must be positive"
    assert DAILY_LOSS_LIMIT > 0,      "DAILY_LOSS_LIMIT must be positive"
    assert EMA_FAST < EMA_SLOW,       "EMA_FAST must be less than EMA_SLOW"
    assert INSTRUMENT in ("NIFTY", "BANKNIFTY"), "INSTRUMENT must be NIFTY or BANKNIFTY"
    assert MARKET_OPEN < NO_TRADE_AFTER < MARKET_CLOSE, "Invalid market hours"


validate()
