import os
from dotenv import load_dotenv

load_dotenv()

# ── Credentials ───────────────────────────────────────────────────────────────
API_KEY        = os.getenv("KITE_API_KEY",    "")
API_SECRET     = os.getenv("KITE_API_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY",  "")

# ── JWT Auth ───────────────────────────────────────────────────────────────────
JWT_SECRET       = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", "")
DB_NAME   = "algo_trader"

# ── CORS — set to your Netlify URL in production ──────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

# ── Algo engine (kite_trader_app) ─────────────────────────────────────────────
ALGO_ENGINE_URL = os.getenv("ALGO_ENGINE_URL", "http://localhost:5050")

# ── Trading ───────────────────────────────────────────────────────────────────
PAPER_TRADING         = os.getenv("PAPER_TRADING", "true").lower() == "true"
INSTRUMENT            = os.getenv("INSTRUMENT", "NIFTY")
TIMEFRAME             = int(os.getenv("TIMEFRAME", "5"))
CAPITAL               = float(os.getenv("CAPITAL", "240000"))
PROFIT_VAULT          = float(os.getenv("PROFIT_VAULT", "0"))
RISK_PCT              = float(os.getenv("RISK_PCT", "0.03"))
MAX_TRADES_DAY        = int(os.getenv("MAX_TRADES_DAY", "10"))  # max losing trades before stop
DAILY_LOSS_LIMIT      = float(os.getenv("DAILY_LOSS_LIMIT", "8500"))

# ── Runtime safety / polling ─────────────────────────────────────────────────
# Signal generation must use only fully closed candles. 5m candle timestamps are
# candle-open times, so the candle is closed only after timestamp + 5 minutes.
CANDLE_CLOSE_DELAY_SECONDS = int(os.getenv("CANDLE_CLOSE_DELAY_SECONDS", "20"))
SIGNAL_POLL_SECONDS        = int(os.getenv("SIGNAL_POLL_SECONDS", "10"))
MONITOR_INTERVAL_SECONDS   = int(os.getenv("MONITOR_INTERVAL_SECONDS", "5"))
IDLE_MONITOR_SECONDS       = int(os.getenv("IDLE_MONITOR_SECONDS", "15"))

# ── EMA ───────────────────────────────────────────────────────────────────────
EMA_FAST = int(os.getenv("EMA_FAST", "8"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "30"))

# ── Candle patterns ───────────────────────────────────────────────────────────
DOMINANCE_BODY = float(os.getenv("DOMINANCE_BODY", "0.55"))
REJECTION_WICK = float(os.getenv("REJECTION_WICK", "0.45"))

# ── Filters ───────────────────────────────────────────────────────────────────
ADX_THRESHOLD   = float(os.getenv("ADX_THRESHOLD", "0"))    # transcript mein ADX nahi tha
EMA30_PROXIMITY = float(os.getenv("EMA30_PROXIMITY", "0.006"))
STRETCH_PCT     = float(os.getenv("STRETCH_PCT", "0.001"))
SL_BUFFER       = float(os.getenv("SL_BUFFER", "0"))       # transcript: SL = candle low, no buffer
ENTRY_BUFFER    = float(os.getenv("ENTRY_BUFFER", "0"))     # transcript: entry = candle high exactly
OPT_SL_PCT      = float(os.getenv("OPT_SL_PCT",  "0.40"))
OI_BUFFER       = float(os.getenv("OI_BUFFER", "50"))

# ── Market hours (IST 24h) ────────────────────────────────────────────────────
MARKET_OPEN         = "09:15"
MARKET_CLOSE        = "15:20"
NO_TRADE_AFTER      = "15:00"
SQUARE_OFF_TIME     = os.getenv("SQUARE_OFF_TIME", "15:15")
OPEN_VOLATILITY_END = "09:45"

# ── Notifications ─────────────────────────────────────────────────────────────
WHATSAPP_PHONE  = os.getenv("WHATSAPP_PHONE",  "")
WHATSAPP_APIKEY = os.getenv("WHATSAPP_APIKEY", "")
