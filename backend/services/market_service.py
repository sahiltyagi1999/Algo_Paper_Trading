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
        import yfinance as yf
        import logging as _logging
        _yf = _logging.getLogger("yfinance")
        _prev = _yf.level
        _yf.setLevel(_logging.CRITICAL)
        t = yf.Ticker("^INDIAVIX")
        hist = t.history(period="1d", interval="1m")
        _yf.setLevel(_prev)
        if not hist.empty:
            vix = float(hist["Close"].iloc[-1])
            status = next(label for threshold, label in _VIX_LEVELS if vix >= threshold)
            return {"vix": round(vix, 2), "status": status}
    except Exception as e:
        log.warning(f"VIX fetch failed: {e}")
    return {"vix": None, "status": "UNKNOWN"}


def get_oi() -> dict:
    try:
        from core.database import load_access_token
        from kiteconnect import KiteConnect
        import config as cfg
        token_info = load_access_token()
        if not token_info:
            return {}
        kite = KiteConnect(api_key=cfg.API_KEY)
        kite.set_access_token(token_info[0])

        strike_gap = 100 if config.INSTRUMENT == "BANKNIFTY" else 50
        # Get spot price
        idx_symbol = "NSE:NIFTY 50" if config.INSTRUMENT == "NIFTY" else "NSE:NIFTY BANK"
        spot = float(kite.quote([idx_symbol])[idx_symbol]["last_price"])
        atm = int(round(spot / strike_gap) * strike_gap)

        # Fetch option chain for ±10 strikes
        strikes = range(atm - strike_gap * 10, atm + strike_gap * 11, strike_gap)
        expiry = _nearest_expiry(kite, config.INSTRUMENT)
        if not expiry:
            return {}

        oi_data = {}
        for strike in strikes:
            for opt in ("CE", "PE"):
                sym = f"{config.INSTRUMENT}{expiry}{strike}{opt}"
                try:
                    q = kite.quote([f"NFO:{sym}"])
                    oi_data[(strike, opt)] = q[f"NFO:{sym}"].get("oi", 0)
                except Exception:
                    oi_data[(strike, opt)] = 0

        call_oi = {s: oi_data.get((s, "CE"), 0) for s in strikes}
        put_oi  = {s: oi_data.get((s, "PE"), 0) for s in strikes}
        max_call_strike = max(call_oi, key=call_oi.get)
        max_put_strike  = max(put_oi,  key=put_oi.get)
        total_call = sum(call_oi.values())
        total_put  = sum(put_oi.values())
        pcr = round(total_put / total_call, 2) if total_call else 0
        bias = "BULLISH" if pcr > 1.2 else "BEARISH" if pcr < 0.8 else "NEUTRAL"
        return {
            "resistance": max_call_strike,
            "support":    max_put_strike,
            "max_pain":   atm,
            "pcr":        pcr,
            "bias":       bias,
            "expiry":     expiry,
        }
    except Exception as e:
        log.warning(f"OI fetch failed: {e}")
        return {}


def _nearest_expiry(kite, instrument: str) -> str | None:
    try:
        from datetime import date
        instruments = kite.instruments("NFO")
        name = "NIFTY" if instrument == "NIFTY" else "BANKNIFTY"
        today = date.today()
        expiries = sorted(set(
            i["expiry"] for i in instruments
            if i["name"] == name and i["instrument_type"] in ("CE", "PE")
            and i["expiry"] and i["expiry"] >= today
        ))
        if not expiries:
            return None
        d = expiries[0]
        return d.strftime("%y%b%d").upper()
    except Exception:
        return None


_YAHOO_MAP = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}

def get_candles() -> list[dict]:
    try:
        import yfinance as yf
        import pandas as pd
        import logging as _logging
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))

        # Suppress yfinance's noisy error output (market closed / weekend)
        _yf_log = _logging.getLogger("yfinance")
        _prev_level = _yf_log.level
        _yf_log.setLevel(_logging.CRITICAL)

        ticker = _YAHOO_MAP.get(config.INSTRUMENT, "^NSEI")
        # Use 5d so we always get data even if today started recently;
        # then keep only today's IST candles
        df = yf.download(ticker, period="5d", interval="5m", progress=False, auto_adjust=True)
        _yf_log.setLevel(_prev_level)

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
        # Keep only today's candles (IST date)
        today_ist = date.today().isoformat()
        df = df[df.index.strftime("%Y-%m-%d") == today_ist]
        if df.empty:
            return []
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
