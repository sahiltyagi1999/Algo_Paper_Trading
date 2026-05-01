"""
services/market_service.py
VIX, OI levels, candles, and algo status.
All data comes from MongoDB — no local file fallbacks.
"""
import logging
from datetime import date, datetime

import config
from core import database as db

log = logging.getLogger(__name__)

_VIX_LEVELS = [
    (30, "DANGEROUS"),
    (25, "HIGH"),
    (20, "ELEVATED"),
    (12, "NORMAL"),
    (0,  "VERY_LOW"),
]


def get_vix() -> dict:
    try:
        from iv_filter import fetch_india_vix
        vix = fetch_india_vix()
        if not vix:
            return {"vix": None, "status": "UNKNOWN"}
        status = next(label for threshold, label in _VIX_LEVELS if vix >= threshold)
        return {"vix": vix, "status": status}
    except Exception as e:
        log.warning(f"VIX fetch failed: {e}")
        return {"vix": None, "status": "UNKNOWN"}


def get_oi() -> dict:
    try:
        from oi_data import get_oi_levels
        return get_oi_levels(config.INSTRUMENT) or {}
    except Exception as e:
        log.warning(f"OI fetch failed: {e}")
        return {}


_YAHOO_MAP = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}

def get_candles() -> list[dict]:
    try:
        import yfinance as yf
        import pandas as pd
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))

        ticker = _YAHOO_MAP.get(config.INSTRUMENT, "^NSEI")
        df = yf.download(ticker, period="1d", interval="5m", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return []
        # Flatten MultiIndex columns (yfinance >= 0.2.x)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close"]].dropna()
        # Convert UTC index → IST for correct time display
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)
        df["ema8"]  = df["close"].ewm(span=8,  adjust=False).mean()
        df["ema30"] = df["close"].ewm(span=30, adjust=False).mean()
        return [
            {
                "t":     ts.strftime("%H:%M"),
                "o":     round(float(row["open"]),  2),
                "h":     round(float(row["high"]),  2),
                "l":     round(float(row["low"]),   2),
                "c":     round(float(row["close"]), 2),
                "ema8":  round(float(row["ema8"]),  2),
                "ema30": round(float(row["ema30"]), 2),
            }
            for ts, row in df.iterrows()
        ]
    except Exception as e:
        log.warning(f"Candle fetch failed: {e}")
        return []


def get_algo_status() -> dict:
    running  = False
    last_log = ""
    if db.is_connected():
        lines = db.get_logs(limit=1)
        if lines:
            last_log = lines[-1]
            try:
                log_time = datetime.strptime(last_log[:19], "%Y-%m-%d %H:%M:%S")
                running  = (datetime.now() - log_time).total_seconds() < 120
            except ValueError:
                pass
    return {"running": running, "last_log": last_log}


def get_logs(log_date: str = "", limit: int = 300) -> dict:
    today = log_date or date.today().isoformat()
    if db.is_connected():
        return {"lines": db.get_logs(today, limit), "source": "mongodb"}
    return {"lines": [], "source": "mongodb_disconnected"}
