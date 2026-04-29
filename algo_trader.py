"""
8-30 EMA Algo Trader — Paper Trading Mode
==========================================
Run every morning AFTER logging in:
    python3 algo_trader.py

Flow:
  1. Pre-market checks (news, VIX, OI)
  2. Wait for 9:15 AM
  3. Fetch live candles every 5 min via Zerodha
  4. Detect EMA signals + apply all filters
  5. Paper trade automatically
  6. Print daily report at 3:20 PM
"""

import logging
import os
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

import config
import report
from candle_patterns import is_bullish, is_bearish, is_dominance, is_rejection
from iv_filter import get_vix_status
from news_filter import is_high_impact_news_day, should_pause_trading, is_expiry_week
from oi_data import get_oi_levels, is_trade_aligned_with_oi
from option_chain import fetch_option_price, get_option_sl_target
import paper_trade
from paper_trade import PaperTradeEngine
from zerodha_login import get_kite

# ── Logging Setup ──────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
_daily_log = f"logs/algo_{date.today()}.log"
_fmt       = "%(asctime)s  %(levelname)-8s  %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=_fmt,
    handlers=[
        logging.FileHandler(config.LOG_FILE),   # master log (all days)
        logging.FileHandler(_daily_log),         # today only
        logging.StreamHandler(),                 # terminal
    ],
)
log = logging.getLogger(__name__)

# ── Kite Interval Map ──────────────────────────────────────────────────────────
_KITE_INTERVALS = {1: "minute", 5: "5minute", 15: "15minute", 60: "60minute"}
_INDEX_TOKENS   = {"NIFTY": 256265, "BANKNIFTY": 260105}


# ── Data Fetching ──────────────────────────────────────────────────────────────

def get_index_token(kite, symbol: str) -> int:
    try:
        instruments = kite.instruments("NSE")
        label       = "NIFTY 50" if symbol == "NIFTY" else "NIFTY BANK"
        for ins in instruments:
            if ins.get("tradingsymbol") == label:
                return ins["instrument_token"]
    except Exception as e:
        log.warning(f"Token lookup failed ({e}), using fallback")
    return _INDEX_TOKENS[symbol]


def fetch_candles(kite, token: int, interval: str,
                  lookback_days: int = 2) -> pd.DataFrame | None:
    try:
        from_dt = datetime.now() - timedelta(days=lookback_days)
        data    = kite.historical_data(token, from_dt, datetime.now(), interval)
        if not data:
            return None
        df = pd.DataFrame(data).set_index("date")
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        log.error(f"Candle fetch failed: {e}")
        return None


# ── Indicators ─────────────────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df        = df.copy()
    df["ema8"]  = df["close"].ewm(span=config.EMA_FAST, adjust=False).mean()
    df["ema30"] = df["close"].ewm(span=config.EMA_SLOW, adjust=False).mean()

    # ADX (14-period)
    high, low, close = df["high"], df["low"], df["close"]
    pdm = high.diff().clip(lower=0)
    ndm = (-low.diff()).clip(lower=0)
    tr  = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr14  = tr.ewm(span=14, adjust=False).mean()
    pdi    = 100 * pdm.ewm(span=14, adjust=False).mean() / atr14
    ndi    = 100 * ndm.ewm(span=14, adjust=False).mean() / atr14
    dx     = (100 * (pdi - ndi).abs() / (pdi + ndi)).fillna(0)
    df["adx"] = dx.ewm(span=14, adjust=False).mean()

    df["direction"] = np.where(df["ema8"] > df["ema30"], "BUY", "SELL")
    df["stretched"] = ((df["ema8"] - df["ema30"]).abs() / df["close"]) >= config.STRETCH_PCT
    return df


# ── Signal Detection ───────────────────────────────────────────────────────────

def detect_signal(df: pd.DataFrame) -> dict | None:
    if len(df) < config.EMA_SLOW + 5:
        return None

    row       = df.iloc[-1]
    direction = row["direction"]
    now_str   = datetime.now().strftime("%H:%M")

    if row["adx"] < config.ADX_THRESHOLD:
        log.debug(f"ADX={row['adx']:.1f} < {config.ADX_THRESHOLD} — sideways, skip")
        return None

    if now_str >= config.NO_TRADE_AFTER:
        return None

    near_ema30  = (abs(row["close"] - row["ema30"]) / row["ema30"]) <= config.EMA30_PROXIMITY
    good_candle = is_dominance(row) or is_rejection(row)
    body_pct    = abs(row["close"] - row["open"]) / (row["high"] - row["low"]) if (row["high"] - row["low"]) else 0
    gap_pct     = abs(row["ema8"] - row["ema30"]) / row["close"]

    log.info(
        f"Signal scan | Dir={direction} ADX={row['adx']:.1f} "
        f"near_ema30={near_ema30}({abs(row['close']-row['ema30'])/row['ema30']*100:.2f}%) "
        f"good_candle={good_candle}(body={body_pct*100:.0f}%) "
        f"stretched={row['stretched']}(gap={gap_pct*100:.2f}%)"
    )

    # Entry 1 — Retest
    if near_ema30 and good_candle:
        if direction == "BUY" and is_bullish(row):
            sl     = row["low"] - config.SL_BUFFER
            entry  = row["high"] + config.ENTRY_BUFFER
            return _signal("BUY", "Retest", entry, sl, rr=3, row=row)
        if direction == "SELL" and is_bearish(row):
            sl    = row["high"] + config.SL_BUFFER
            entry = row["low"] - config.ENTRY_BUFFER
            return _signal("SELL", "Retest", entry, sl, rr=3, row=row)

    # Entry 2 — Continuation
    if row["stretched"] and is_dominance(row):
        if direction == "BUY" and is_bullish(row):
            sl    = row["low"] - config.SL_BUFFER
            entry = row["high"] + config.ENTRY_BUFFER
            return _signal("BUY", "Continuation", entry, sl, rr=2, row=row)
        if direction == "SELL" and is_bearish(row):
            sl    = row["high"] + config.SL_BUFFER
            entry = row["low"] - config.ENTRY_BUFFER
            return _signal("SELL", "Continuation", entry, sl, rr=2, row=row)

    return None


def _signal(direction, entry_type, entry, sl, rr, row) -> dict:
    risk   = abs(entry - sl)
    target = (entry + risk * rr) if direction == "BUY" else (entry - risk * rr)
    return {
        "direction"  : direction,
        "entry_type" : entry_type,
        "entry"      : round(entry, 2),
        "sl"         : round(sl, 2),
        "target"     : round(target, 2),
        "rr"         : rr,
        "candle_time": str(row.name),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _calc_lots(capital: float, risk_pct: float, multiplier: float,
               opt_risk_per_lot: float) -> int:
    if opt_risk_per_lot <= 0:
        return 1
    risk_amt = capital * risk_pct * multiplier
    return max(1, int(risk_amt / opt_risk_per_lot))


def _time_mins(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def wait_for_market_open():
    open_m = _time_mins(config.MARKET_OPEN)
    while True:
        now = datetime.now()
        if now.weekday() >= 5:
            log.info("Weekend — waiting...")
            time.sleep(3600)
            continue
        current_m = now.hour * 60 + now.minute
        if current_m >= open_m:
            break
        wait_s = (open_m - current_m) * 60 - now.second
        log.info(f"Market opens at {config.MARKET_OPEN}. Waiting {wait_s // 60} min...")
        time.sleep(min(wait_s, 60))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 55)
    log.info("  8-30 EMA ALGO TRADER — PAPER TRADING MODE")
    log.info("=" * 55)

    kite = get_kite()
    paper_trade.set_kite(kite)   # so engine can fetch live option prices at exit

    token    = get_index_token(kite, config.INSTRUMENT)
    interval = _KITE_INTERVALS.get(config.TIMEFRAME, "5minute")
    log.info(f"Instrument={config.INSTRUMENT} Token={token} Interval={interval}")

    # ── Pre-market Checks ──────────────────────────────────────────────────────
    if is_expiry_week():
        log.info("*** EXPIRY WEEK — market may be choppy, fewer signals expected ***")
    log.info("Running pre-market checks...")

    dangerous, reason = is_high_impact_news_day()
    if dangerous:
        log.warning(f"SKIPPING TODAY: {reason}")
        print(f"\n  Algo will NOT trade today.\n  Reason: {reason}\n")
        return

    vix_status = get_vix_status()
    log.info(f"VIX: {vix_status['message']}")
    if not vix_status["safe"]:
        log.warning(f"SKIPPING TODAY: {vix_status['message']}")
        print(f"\n  Algo will NOT trade today.\n  Reason: {vix_status['message']}\n")
        return

    oi_levels        = get_oi_levels(config.INSTRUMENT, kite=kite)
    oi_last_refresh  = datetime.now()
    log.info(f"Pre-market OK | VIX={vix_status['vix']} | "
             f"OI bias={oi_levels['bias'] if oi_levels else 'N/A'}")

    wait_for_market_open()
    log.info("Market open. Algo running...")

    engine           = PaperTradeEngine()
    last_candle_time = None
    close_m          = _time_mins(config.MARKET_CLOSE)
    current_date     = date.today()

    # ── Main Loop ──────────────────────────────────────────────────────────────
    while True:
        now     = datetime.now()
        current_m = now.hour * 60 + now.minute

        # Reset daily counters when date rolls over (multi-day run)
        if now.date() != current_date:
            engine.reset_daily()
            current_date     = now.date()
            last_candle_time = None
            log.info(f"New trading day: {current_date}")

        if current_m >= close_m:
            log.info("Market closed — closing open trades")
            df = fetch_candles(kite, token, interval)
            if df is not None and len(df):
                engine.close_all(df.iloc[-1]["close"])
            break

        # Refresh OI every 30 min
        if (datetime.now() - oi_last_refresh).total_seconds() >= 1800:
            _spot_now       = df.iloc[-1]["close"] if df is not None and len(df) else 0
            oi_levels       = get_oi_levels(config.INSTRUMENT, kite=kite, spot=_spot_now)
            oi_last_refresh = datetime.now()
            log.info(f"OI refreshed | {oi_levels}")

        df = fetch_candles(kite, token, interval)
        if df is None or len(df) == 0:
            time.sleep(15)
            continue

        df           = add_indicators(df)
        candle_time  = df.index[-1]

        if candle_time == last_candle_time:
            time.sleep(10)
            continue

        last_candle_time = candle_time
        latest           = df.iloc[-1]

        log.info(
            f"Candle {candle_time} | Close={latest['close']:.2f} | "
            f"EMA8={latest['ema8']:.2f} EMA30={latest['ema30']:.2f} | "
            f"ADX={latest['adx']:.1f} Dir={latest['direction']}"
        )

        # Check open trades
        for closed in engine.check_trades(latest["high"], latest["low"], latest["close"]):
            report.print_trade_alert(closed, "EXIT")

        # New signal — only when no open trades
        if len(engine.open_trades) > 0:
            time.sleep(15)
            continue

        paused, pause_reason = should_pause_trading()
        if paused:
            log.info(f"Paused: {pause_reason}")
            time.sleep(15)
            continue

        signal = detect_signal(df)
        if not signal:
            time.sleep(15)
            continue

        if not is_trade_aligned_with_oi(signal["direction"], signal["entry"], oi_levels):
            log.info(f"OI filter blocked {signal['direction']} at {signal['entry']}")
            time.sleep(15)
            continue

        multiplier = vix_status.get("qty_multiplier", 1.0)
        if multiplier == 0.0:
            log.info("VIX multiplier=0 — skipping trade")
            time.sleep(15)
            continue

        # Fetch real option price via Kite API
        opt_data = fetch_option_price(
            config.INSTRUMENT, latest["close"], signal["direction"], kite=kite
        )

        if opt_data is None or opt_data["ltp"] <= 0:
            log.warning("Option price unavailable — skipping trade")
            time.sleep(15)
            continue

        # Skip illiquid options (very low volume or OI)
        if opt_data["volume"] < 100 or opt_data["oi"] < 500:
            log.warning(f"Option illiquid (Vol={opt_data['volume']} OI={opt_data['oi']}) — skipping")
            time.sleep(15)
            continue

        # Convert spot SL/target to option SL/target using delta
        lot_size   = opt_data["lot_size"]   # real lot size from Kite instruments
        opt_levels = get_option_sl_target(
            option_price  = opt_data["ltp"],
            spot_entry    = signal["entry"],
            spot_sl       = signal["sl"],
            spot_target   = signal["target"],
            direction     = signal["direction"],
            lot_size      = lot_size,
        )

        # Calculate lots based on risk (2% of capital per trade)
        lots = _calc_lots(engine.capital, config.RISK_PCT, multiplier,
                          opt_levels["opt_risk_per_lot"])

        # Hard cap: total cost must never exceed 50% of available capital
        # This prevents over-leveraging when spot SL is very tight (small opt_risk_per_lot)
        max_lots_by_capital = max(1, int((engine.capital * config.MAX_CAPITAL_PER_TRADE) / opt_data["lot_value"]))
        lots = min(lots, max_lots_by_capital)
        qty  = lots * lot_size

        log.info(
            f"Option trade | {opt_data['symbol']} | "
            f"LTP={opt_data['ltp']} SL={opt_levels['option_sl']} "
            f"Target={opt_levels['option_target']} | "
            f"Lots={lots} Qty={qty} LotValue=Rs.{opt_data['lot_value']}"
        )

        trade, status = engine.place_order(
            direction  = signal["direction"],
            entry      = opt_levels["option_entry"],   # real option premium
            sl         = opt_levels["option_sl"],       # option-based SL
            target     = opt_levels["option_target"],   # option-based target
            rr         = signal["rr"],
            entry_type = signal["entry_type"],
            symbol     = opt_data["symbol"],            # real option symbol
            qty        = qty,                           # in lots × lot size
        )

        if trade:
            trade["spot_entry"]      = signal["entry"]
            trade["spot_sl"]         = signal["sl"]
            trade["spot_target"]     = signal["target"]
            trade["ltp_at_entry"]    = opt_data["ltp"]
            trade["bid_at_entry"]    = opt_data["bid"]
            trade["ask_at_entry"]    = opt_data["ask"]
            trade["oi_at_entry"]     = opt_data["oi"]
            trade["volume_at_entry"] = opt_data["volume"]
            trade["opt_type"]        = opt_data["opt_type"]
            trade["lots"]            = lots
            report.print_trade_alert(trade, "ENTRY")
        else:
            log.info(f"Order blocked: {status}")

        # Hourly live summary
        if now.minute == 0:
            s = engine.summary()
            log.info(f"Hourly | Trades={s['total_trades']} "
                     f"PnL=Rs.{s['daily_pnl']:,.2f} WinRate={s['win_rate']}%")

        time.sleep(15)

    # ── End of Day ─────────────────────────────────────────────────────────────
    summary = engine.summary()
    report.print_daily_report(
        summary,
        vix        = vix_status.get("vix"),
        oi_levels  = oi_levels,
        all_trades = engine.closed_trades,
    )
    log.info("Algo stopped. See you tomorrow!")


if __name__ == "__main__":
    main()
