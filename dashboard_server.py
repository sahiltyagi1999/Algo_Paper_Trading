"""
Dashboard Server
Serves live trading data to the web dashboard.
Run alongside algo_trader.py:
    python3 dashboard_server.py
Then open: http://localhost:4200
"""
import csv
import json
import logging
import os
from datetime import date, datetime

from flask import Flask, jsonify, render_template

import config
from iv_filter import fetch_india_vix
from oi_data import get_oi_levels

log = logging.getLogger(__name__)
app = Flask(__name__)


# ── Data Helpers ───────────────────────────────────────────────────────────────

def _read_trades() -> list[dict]:
    if not os.path.exists(config.REPORT_FILE):
        return []
    try:
        with open(config.REPORT_FILE, newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def _todays_trades() -> list[dict]:
    today = date.today().isoformat()
    return [t for t in _read_trades() if today in t.get("date", "")]


def _equity_curve(trades: list[dict]) -> list[dict]:
    equity = float(config.CAPITAL)
    curve  = [{"x": "Start", "y": equity}]
    for t in trades:
        equity += float(t.get("pnl") or 0)
        curve.append({"x": t.get("date", "")[:16], "y": round(equity, 2)})
    return curve


def _summary(trades: list[dict]) -> dict:
    closed   = [t for t in trades if t.get("status") not in ("OPEN", "")]
    wins     = [t for t in closed if t.get("status") == "TARGET_HIT"]
    losses   = [t for t in closed if t.get("status") == "SL_HIT"]
    total_pnl = sum(float(t.get("pnl") or 0) for t in closed)
    win_rate  = round(len(wins) / len(closed) * 100, 1) if closed else 0.0
    return {
        "total_trades": len(closed),
        "wins"        : len(wins),
        "losses"      : len(losses),
        "win_rate"    : win_rate,
        "total_pnl"   : round(total_pnl, 2),
        "capital"     : round(float(config.CAPITAL) + total_pnl, 2),
        "open_trades" : len([t for t in trades if t.get("status") == "OPEN"]),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html",
        instrument = config.INSTRUMENT,
        capital    = config.CAPITAL,
        risk_pct   = config.RISK_PCT,
        max_trades = config.MAX_TRADES_DAY,
        loss_limit = config.DAILY_LOSS_LIMIT,
        timeframe  = config.TIMEFRAME,
    )


@app.route("/api/summary")
def api_summary():
    return jsonify({
        "all"  : _summary(_read_trades()),
        "today": _summary(_todays_trades()),
    })


@app.route("/api/trades")
def api_trades():
    trades = _read_trades()
    trades.reverse()
    return jsonify(trades[:50])


@app.route("/api/equity")
def api_equity():
    return jsonify(_equity_curve(_read_trades()))


@app.route("/api/todays_equity")
def api_todays_equity():
    return jsonify(_equity_curve(_todays_trades()))


@app.route("/api/vix")
def api_vix():
    vix = fetch_india_vix()
    if not vix:
        return jsonify({"vix": None, "status": "UNKNOWN"})
    status = ("DANGEROUS" if vix >= 30 else "HIGH"      if vix >= 25
              else "ELEVATED" if vix >= 20 else "NORMAL" if vix >= 12
              else "VERY_LOW")
    return jsonify({"vix": vix, "status": status})


@app.route("/api/oi")
def api_oi():
    return jsonify(get_oi_levels(config.INSTRUMENT) or {})


@app.route("/api/daily_history")
def api_daily_history():
    history = []
    if os.path.exists("logs"):
        for fname in sorted(os.listdir("logs")):
            if fname.startswith("summary_") and fname.endswith(".json"):
                try:
                    with open(os.path.join("logs", fname)) as f:
                        history.append(json.load(f))
                except (OSError, json.JSONDecodeError) as e:
                    log.warning(f"Skipping corrupt summary file {fname}: {e}")
    return jsonify(history)


@app.route("/api/candles")
def api_candles():
    """Live NIFTY 5-min candles with EMA8/EMA30 for the candlestick chart."""
    try:
        from zerodha_login import get_kite
        from algo_trader import fetch_candles, add_indicators, get_index_token
        kite     = get_kite()
        token    = get_index_token(kite, config.INSTRUMENT)
        df       = fetch_candles(kite, token, "5minute", lookback_days=1)
        if df is None or df.empty:
            return jsonify([])
        df = add_indicators(df)
        # Keep only today's candles
        today = date.today().isoformat()
        df    = df[df.index.strftime("%Y-%m-%d") == today]
        result = []
        for ts, row in df.iterrows():
            result.append({
                "t"    : ts.strftime("%H:%M"),
                "o"    : round(float(row["open"]),  2),
                "h"    : round(float(row["high"]),  2),
                "l"    : round(float(row["low"]),   2),
                "c"    : round(float(row["close"]), 2),
                "ema8" : round(float(row["ema8"]),  2),
                "ema30": round(float(row["ema30"]), 2),
            })
        return jsonify(result)
    except Exception as e:
        log.warning(f"Candle API failed: {e}")
        return jsonify([])


@app.route("/api/status")
def api_status():
    running  = False
    last_log = ""
    if os.path.exists(config.LOG_FILE):
        try:
            with open(config.LOG_FILE) as f:
                lines = f.readlines()
            if lines:
                last_log     = lines[-1].strip()
                log_time_str = last_log[:19]
                log_time     = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                running      = (datetime.now() - log_time).total_seconds() < 120
        except (OSError, ValueError):
            pass
    return jsonify({"running": running, "last_log": last_log})


if __name__ == "__main__":
    print("\n" + "=" * 45)
    print("  DASHBOARD at http://localhost:4200")
    print("=" * 45 + "\n")
    app.run(debug=False, port=4200, use_reloader=False)
