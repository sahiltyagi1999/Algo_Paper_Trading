from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
import config

SYMBOL_MAP = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
STRIKE_GAP = {"NIFTY": 50, "BANKNIFTY": 100}
LOT_SIZE   = {"NIFTY": 65, "BANKNIFTY": 15}
INTERVAL_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}


def fetch_candles_yahoo(instrument: str = "NIFTY", period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    ticker = SYMBOL_MAP.get(instrument, "^NSEI")
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.dropna(inplace=True)
    return df


def closed_candles(df: pd.DataFrame, interval: str = "5m",
                   now: datetime | None = None,
                   settle_seconds: int | None = None) -> pd.DataFrame:
    """
    Return only fully closed candles.

    yfinance timestamps 5m candles at candle-open time. At 10:05:05 the
    10:05 candle is still forming, so using df.iloc[-1] can produce false
    "No signal" decisions. This helper keeps rows where:
        candle_open + interval <= now - settle_delay
    """
    if df.empty:
        return df

    seconds = INTERVAL_SECONDS.get(interval, 300)
    settle = config.CANDLE_CLOSE_DELAY_SECONDS if settle_seconds is None else settle_seconds
    now_utc = now or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    out = df.copy()
    idx = out.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")

    cutoff = now_utc - pd.Timedelta(seconds=settle)
    closed_mask = idx + pd.Timedelta(seconds=seconds) <= cutoff
    out = out.loc[closed_mask].copy()
    out.attrs["dropped_forming_candles"] = int((~closed_mask).sum())
    out.attrs["latest_raw_candle"] = df.index[-1] if len(df.index) else None
    return out


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < config.EMA_SLOW:
        return df
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=config.EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=config.EMA_SLOW, adjust=False).mean()
    df["adx"]      = _compute_adx(df)
    return df


def _compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    plus_dm  = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr      = tr.ewm(span=period, adjust=False).mean()
    plus_di  = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    return dx.ewm(span=period, adjust=False).mean()


def get_atm_strike(spot: float, instrument: str = "NIFTY") -> int:
    gap = STRIKE_GAP.get(instrument, 50)
    return int(round(spot / gap) * gap)


def get_spot_price(instrument: str = "NIFTY") -> float | None:
    ticker = SYMBOL_MAP.get(instrument, "^NSEI")
    try:
        hist = yf.Ticker(ticker).history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


def fetch_live_option_price(kite, symbol: str) -> dict | None:
    try:
        q    = kite.quote([f"NFO:{symbol}"])
        data = q.get(f"NFO:{symbol}", {})
        return {
            "ltp":    data.get("last_price", 0),
            "bid":    data.get("depth", {}).get("buy",  [{}])[0].get("price", 0),
            "ask":    data.get("depth", {}).get("sell", [{}])[0].get("price", 0),
            "oi":     data.get("oi", 0),
            "volume": data.get("volume", 0),
        }
    except Exception:
        return None


def find_atm_option(kite, instrument: str, spot: float, opt_type: str) -> dict | None:
    """
    Resolve the actual Kite tradingsymbol for the nearest ATM option.
    This avoids hand-rolling weekly expiry symbols, which changes by exchange
    format and is unsafe for real trading.
    """
    if kite is None:
        return None
    try:
        strike = get_atm_strike(spot, instrument)
        instruments = kite.instruments("NFO")
        today = datetime.now().date()
        rows = [
            i for i in instruments
            if i.get("name") == instrument
            and i.get("instrument_type") == opt_type
            and float(i.get("strike") or 0) == float(strike)
            and i.get("expiry")
            and i["expiry"] >= today
        ]
        if not rows:
            return None
        rows.sort(key=lambda r: r["expiry"])
        row = rows[0]
        quote = fetch_live_option_price(kite, row["tradingsymbol"]) or {}
        return {
            "symbol": row["tradingsymbol"],
            "strike": strike,
            "expiry": row["expiry"],
            "lot_size": int(row.get("lot_size") or LOT_SIZE.get(instrument, 65)),
            "ltp": float(quote.get("ltp") or 0),
            "bid": quote.get("bid", 0),
            "ask": quote.get("ask", 0),
            "oi": quote.get("oi", 0),
            "volume": quote.get("volume", 0),
        }
    except Exception:
        return None


def fetch_india_vix() -> float | None:
    try:
        import requests
        r = requests.get(
            "https://www.nseindia.com/api/allIndices",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=5,
        )
        for item in r.json().get("data", []):
            if item.get("index") == "INDIA VIX":
                return float(item["last"])
    except Exception:
        pass
    return None
