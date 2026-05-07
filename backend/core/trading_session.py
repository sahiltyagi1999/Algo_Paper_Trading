"""
Trading session manager.
One session = one trading day. Manages start/stop and the background trading loop.

Two threads:
  _run_loop    — polls newly closed 5-min candles, checks range exits, then signals once
  _run_monitor — checks open trade SL/Target using live spot
"""

import uuid, datetime, threading, time, logging
import config
import core.market_data as md
from core.paper_engine import PaperEngine
from core.strategy_engine import explain_signal_ema, get_strategy_runner

logger = logging.getLogger("trading")

_active_session: dict | None = None
_session_thread: threading.Thread | None = None
_monitor_thread: threading.Thread | None = None
_stop_flag = threading.Event()

CANDLE_INTERVAL  = 300  # 5-min candles


def get_active_session() -> dict | None:
    return _active_session


def start_session(settings: dict, kite=None, save_session_fn=None, find_strategy_fn=None,
                  save_trade_fn=None, update_trade_fn=None, open_trades: list = None,
                  restored_pnl: float = 0.0) -> dict:
    global _active_session, _session_thread, _monitor_thread, _stop_flag

    if _active_session and _active_session.get("running"):
        return {"status": "error", "message": "Session already running"}

    session_id = str(uuid.uuid4())[:8]
    paper      = settings.get("paper_trading", True)
    instrument = settings.get("instrument", config.INSTRUMENT)
    capital    = float(settings.get("capital", config.CAPITAL))
    strategy   = settings.get("strategy", "8-30 EMA")
    openai_key = settings.get("openai_api_key", config.OPENAI_API_KEY)
    daily_loss = float(settings.get("daily_loss_limit", config.DAILY_LOSS_LIMIT))
    max_trades = int(settings.get("max_trades_day", config.MAX_TRADES_DAY))

    engine = PaperEngine(
        session_id, capital, daily_loss, max_trades,
        on_trade_save=save_trade_fn,
        on_trade_update=update_trade_fn,
        restored_trades=open_trades or [],
        restored_pnl=restored_pnl,
    ) if paper else None

    _active_session = {
        "session_id": session_id,
        "started_at": datetime.datetime.now().isoformat(),
        "instrument": instrument,
        "paper":      paper,
        "capital":    capital,
        "strategy":   strategy,
        "running":    True,
        "logs":       [],
        "engine":     engine,
        "kite":       kite,
        "settings":   settings,
        "last_signal_candle": None,
        "last_risk_candle": None,
        "last_signal_diag": None,
        "last_data_status": {},
    }

    if save_session_fn:
        _persist_session(save_session_fn)

    _stop_flag.clear()
    signal_runner = get_strategy_runner(strategy, openai_key, find_strategy=find_strategy_fn)

    _session_thread = threading.Thread(
        target=_run_loop,
        args=(_active_session, signal_runner, _stop_flag, save_session_fn),
        daemon=True,
    )
    _session_thread.start()

    # Paper monitor uses live spot, independent of closed-candle signal logic.
    if paper and engine:
        _monitor_thread = threading.Thread(
            target=_run_monitor,
            args=(_active_session, _stop_flag),
            daemon=True,
        )
        _monitor_thread.start()

    return {"status": "started", "session_id": session_id, "paper": paper}


def stop_session(save_session_fn=None) -> dict:
    global _active_session
    if not _active_session:
        return {"status": "error", "message": "No session running"}
    _stop_flag.set()
    if _active_session.get("engine"):
        kite = _active_session.get("kite")
        spot = float(_active_session.get("last_spot") or 0)
        opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, spot)
        _active_session["engine"].close_all(opt_ltp_fn=opt_ltp_fn, source="manual_stop")
    _active_session["running"] = False
    if save_session_fn:
        _persist_session(save_session_fn)
    return {
        "status":  "stopped",
        "summary": _active_session["engine"].summary() if _active_session.get("engine") else {},
    }


def squareoff_now(reason="MANUAL_SQUAREOFF") -> dict:
    session = _active_session
    if not session or not session.get("running"):
        return {"status": "error", "message": "No running session"}
    engine = session.get("engine")
    if not engine:
        return {"status": "error", "message": "No paper engine attached to active session"}
    if not engine.open_trades:
        return {"status": "ok", "message": "No open trades to square off", "summary": engine.summary()}

    kite = session.get("kite")
    instrument = session.get("instrument", config.INSTRUMENT)
    spot = _get_live_spot(kite, instrument)
    if spot > 0:
        session["last_spot"] = spot
        session["last_spot_at"] = datetime.datetime.now().isoformat()
    opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, float(session.get("last_spot") or spot or 0))
    count = _count_open(engine)
    engine.close_all(
        opt_ltp_fn=opt_ltp_fn,
        status="CLOSED_EOD" if reason == "EOD" else "MANUAL_CLOSE",
        reason=reason,
        source=reason.lower(),
    )
    session.pop("pending_signal", None)
    session["engine_summary"] = engine.summary()
    _log(session, f"Square-off now: {count} trade(s) closed | reason={reason} | spot={float(session.get('last_spot') or 0):.2f}")
    return {"status": "closed", "closed": count, "summary": session["engine_summary"]}


def close_trade_now(trade_id: str, exit_price: float | None = None, reason="MANUAL_CLOSE") -> dict:
    session = _active_session
    if not session or not session.get("running"):
        return {"status": "not_active", "message": "No running session"}
    engine = session.get("engine")
    if not engine:
        return {"status": "not_active", "message": "No paper engine attached to active session"}

    open_trade = next((t for t in engine.open_trades if t.get("trade_id") == trade_id), None)
    if not open_trade:
        return {"status": "not_found", "message": "Trade not open in active session"}

    kite = session.get("kite")
    instrument = session.get("instrument", config.INSTRUMENT)
    spot = _get_live_spot(kite, instrument)
    if spot > 0:
        session["last_spot"] = spot
        session["last_spot_at"] = datetime.datetime.now().isoformat()
    opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, float(session.get("last_spot") or spot or 0))
    closed_trade = engine.close_trade(
        trade_id,
        opt_ltp_fn=opt_ltp_fn,
        exit_ltp=exit_price,
        status="MANUAL_CLOSE",
        reason=reason,
        source="manual_close",
    )
    if not closed_trade:
        return {"status": "not_found", "message": "Trade not open in active session"}

    session["engine_summary"] = engine.summary()
    _log(
        session,
        f"Manual close: {closed_trade.get('option_symbol')} @ {closed_trade.get('opt_ltp_exit')} "
        f"| pnl={closed_trade.get('pnl')} | spot={float(session.get('last_spot') or 0):.2f}",
    )
    return {
        "status": "closed",
        "trade": closed_trade,
        "summary": session["engine_summary"],
    }


def _persist_session(save_fn):
    if save_fn and _active_session:
        payload = {k: v for k, v in _active_session.items() if k not in ("engine", "kite")}
        try:
            save_fn(payload)
        except Exception:
            pass


def _log(session: dict, msg: str):
    ts    = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    session["logs"].append(entry)
    if len(session["logs"]) > 300:
        session["logs"] = session["logs"][-300:]
    logger.info(msg)


# ── Monitor thread — checks SL/Target on live spot, independent of candles ────

def _run_monitor(session: dict, stop_flag: threading.Event):
    instrument = session["instrument"]
    engine: PaperEngine = session["engine"]
    kite = session.get("kite")
    lot_size = md.LOT_SIZE.get(instrument, 75)
    _last_spot_log = 0
    _last_error_log = 0
    market_open = _parse_hhmm(config.MARKET_OPEN, datetime.time(9, 15))
    monitor_close = datetime.time(15, 30)
    no_trade_after = _parse_hhmm(config.NO_TRADE_AFTER, datetime.time(15, 0))
    squareoff_time = _parse_hhmm(config.SQUARE_OFF_TIME, datetime.time(15, 15))
    eod_closed = False

    while not stop_flag.is_set():
        now = datetime.datetime.now().time()
        if now >= no_trade_after and session.get("pending_signal"):
            pending = session.pop("pending_signal", None)
            if pending:
                _log(session, f"PENDING cancelled by no-trade window | {pending['direction']} breakout@{pending['breakout_level']}")

        if now >= squareoff_time and engine.open_trades and not eod_closed:
            spot = _get_live_spot(kite, instrument)
            if spot > 0:
                session["last_spot"] = spot
                session["last_spot_at"] = datetime.datetime.now().isoformat()
            opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, float(session.get("last_spot") or spot or 0))
            count = _count_open(engine)
            engine.close_all(opt_ltp_fn=opt_ltp_fn, status="CLOSED_EOD", reason="EOD", source="eod_squareoff")
            eod_closed = True
            session["engine_summary"] = engine.summary()
            _log(session, f"EOD square-off: {count} trade(s) closed | time={now.strftime('%H:%M:%S')} | spot={float(session.get('last_spot') or 0):.2f}")

        if not (market_open <= now <= monitor_close):
            time.sleep(config.IDLE_MONITOR_SECONDS)
            continue
        try:
            spot = _get_live_spot(kite, instrument)
            if spot <= 0:
                if time.time() - _last_error_log >= 60:
                    _log(session, "Live spot unavailable | monitor retrying")
                    _last_error_log = time.time()
                time.sleep(config.MONITOR_INTERVAL_SECONDS)
                continue

            session["last_spot"] = spot
            session["last_spot_at"] = datetime.datetime.now().isoformat()

            # Log live spot every ~1 min
            if time.time() - _last_spot_log >= 60:
                pending = session.get("pending_signal")
                if engine.open_trades:
                    status = "open trade"
                elif pending:
                    status = f"pending {pending['direction']} breakout@{pending['breakout_level']}"
                else:
                    status = "watching"
                _log(session, f"Live spot={spot:.2f} | {status}")
                _last_spot_log = time.time()

            # ── Continuation breakout check ───────────────────────────────
            pending = session.get("pending_signal")
            if pending and now < no_trade_after and not engine.open_trades:
                direction       = pending["direction"]
                breakout_level  = pending["breakout_level"]
                breakout_hit    = (direction == "BUY"  and spot >= breakout_level) or \
                                  (direction == "SELL" and spot <= breakout_level)

                # Expire pending signal after next candle closes (5 min)
                set_at   = datetime.datetime.fromisoformat(pending["set_at"])
                expired  = (datetime.datetime.now() - set_at).total_seconds() > 310

                if breakout_hit:
                    _log(session, f"BREAKOUT {direction} @ spot={spot:.2f} | level={breakout_level}")
                    _place_entry(session, engine, kite, pending, spot, instrument, lot_size)
                    session.pop("pending_signal", None)
                elif expired:
                    _log(session, f"PENDING expired | {direction} breakout@{breakout_level} not hit")
                    session.pop("pending_signal", None)

            # ── SL / Target check on open trades ─────────────────────────
            if not engine.open_trades:
                continue

            closed = _count_open(engine)
            opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, spot)
            engine.check_trades(spot, opt_ltp_fn=opt_ltp_fn)
            newly_closed = closed - _count_open(engine)
            if newly_closed > 0:
                _log(session, f"Monitor: {newly_closed} trade(s) closed | spot={spot:.2f}")
                session["engine_summary"] = engine.summary()
        except Exception as e:
            logger.warning(f"Monitor error: {e}")
        interval = config.MONITOR_INTERVAL_SECONDS if (engine.open_trades or session.get("pending_signal")) else config.IDLE_MONITOR_SECONDS
        time.sleep(interval)


def _place_entry(session, engine, kite, signal, spot, instrument, lot_size):
    direction  = signal["direction"]
    atm        = md.get_atm_strike(spot, instrument)
    opt_type   = "CE" if direction == "BUY" else "PE"
    opt_data   = md.find_atm_option(kite, instrument, spot, opt_type)
    if opt_data:
        opt_symbol = opt_data["symbol"]
        opt_ltp    = opt_data["ltp"] or _get_opt_ltp(kite, opt_data["symbol"], spot)
        lot_size   = int(opt_data.get("lot_size") or lot_size)
    else:
        opt_symbol = f"{instrument}{_next_weekly_expiry()}{atm}{opt_type}"
        opt_ltp    = _get_opt_ltp(kite, opt_symbol, spot)

    if opt_ltp <= 0:
        _log(session, f"ENTRY skipped | {direction} | option LTP unavailable | symbol={opt_symbol}")
        return

    if engine:
        # Both BUY and SELL directions buy options: BUY -> CE, SELL -> PE.
        # Option stop-loss is always below entry premium.
        opt_sl = opt_ltp * (1 - config.OPT_SL_PCT)
        lots   = PaperEngine.calculate_lots(
            engine.capital, opt_ltp, opt_sl, lot_size,
            config.RISK_PCT, config.MAX_CAPITAL_PER_TRADE,
        )
        if lots <= 0:
            risk_per_lot = abs(opt_ltp - opt_sl) * lot_size
            capital_per_lot = opt_ltp * lot_size
            _log(
                session,
                f"ENTRY rejected | {direction} | risk/capital sizing gave 0 lots "
                f"| risk_per_lot={risk_per_lot:.2f} | capital_per_lot={capital_per_lot:.2f} "
                f"| capital={engine.capital:.2f}",
            )
            return
        result = engine.place_order(
            direction=direction,
            instrument=instrument,
            entry_price=signal["entry"],
            sl=signal["sl"],
            target=signal["target"],
            option_symbol=opt_symbol,
            opt_ltp=opt_ltp,
            lots=lots,
            lot_size=lot_size,
            entry_type=signal["entry_type"],
            strategy_name=session["strategy"],
            metadata={
                "execution_spot": spot,
                "option_type": opt_type,
                "option_strike": atm,
                "option_bid": opt_data.get("bid") if opt_data else None,
                "option_ask": opt_data.get("ask") if opt_data else None,
                "option_oi": opt_data.get("oi") if opt_data else None,
                "option_volume": opt_data.get("volume") if opt_data else None,
                "signal_candle_time": signal.get("candle_time"),
                "signal_snapshot": session.get("last_signal_diag"),
            },
        )
        if result["status"] == "placed":
            _log(session, f"ENTRY {direction} | {signal['entry_type']} | {opt_symbol} @ {opt_ltp:.2f} | lots={lots} qty={lots * lot_size} | placed")
        else:
            _log(session, f"ENTRY rejected | {direction} | {signal['entry_type']} | reason={result.get('reason')}")
        session["engine_summary"] = engine.summary()
    else:
        _log(session, f"ENTRY {direction} | {signal['entry_type']} | {opt_symbol} @ {opt_ltp} | LIVE (not implemented)")


def _count_open(engine: PaperEngine) -> int:
    return len(engine.open_trades)


def _parse_hhmm(value: str, fallback: datetime.time) -> datetime.time:
    try:
        hour, minute = str(value).split(":", 1)
        return datetime.time(int(hour), int(minute))
    except Exception:
        return fallback


def _check_closed_candle_exits(session: dict, engine: PaperEngine, kite, candle_ts, candle_row):
    last_risk = session.get("last_risk_candle")
    if last_risk and str(candle_ts) <= str(last_risk):
        return

    session["last_risk_candle"] = str(candle_ts)
    if not engine.open_trades:
        return

    candle_high = float(candle_row["high"])
    candle_low = float(candle_row["low"])
    candle_close = float(candle_row["close"])
    candle_close_time = _candle_close_time(candle_ts)
    opt_ltp_fn = lambda sym: _get_opt_ltp(kite, sym, candle_close)

    before = _count_open(engine)
    events = engine.check_trades_range(
        candle_high=candle_high,
        candle_low=candle_low,
        candle_close=candle_close,
        candle_time=candle_ts,
        candle_close_time=candle_close_time,
        opt_ltp_fn=opt_ltp_fn,
    )
    after = _count_open(engine)
    if events:
        for event in events:
            extra = " | both SL and target touched; SL priority used" if event.get("both_touched") else ""
            _log(
                session,
                f"Closed candle risk check: {event['hit']} | candle={candle_ts} "
                f"| high={candle_high:.2f} low={candle_low:.2f} close={candle_close:.2f}{extra}",
            )
        _log(session, f"Closed candle risk check: {before - after} trade(s) closed")
        session["engine_summary"] = engine.summary()


def _candle_close_time(candle_ts):
    try:
        if hasattr(candle_ts, "to_pydatetime"):
            dt = candle_ts.to_pydatetime()
        elif isinstance(candle_ts, datetime.datetime):
            dt = candle_ts
        else:
            return None
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt + datetime.timedelta(seconds=CANDLE_INTERVAL)
    except Exception:
        return None


def _get_live_spot(kite, instrument: str) -> float:
    """Fast spot price — Kite if connected, else yfinance 1m."""
    if kite:
        try:
            sym = "NSE:NIFTY 50" if instrument == "NIFTY" else "NSE:NIFTY BANK"
            return float(kite.quote([sym])[sym]["last_price"])
        except Exception:
            pass
    try:
        import yfinance as yf
        import logging as _logging
        _yf = _logging.getLogger("yfinance")
        _prev = _yf.level
        _yf.setLevel(_logging.CRITICAL)
        _YAHOO_MAP = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}
        ticker = _YAHOO_MAP.get(instrument, "^NSEI")
        df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=True)
        _yf.setLevel(_prev)
        if df is not None and not df.empty:
            if hasattr(df.columns, "get_level_values"):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            val = df["close"].iloc[-1]
            # handle numpy scalar or Series
            return float(val.iloc[0] if hasattr(val, "iloc") else val)
    except Exception as e:
        logger.warning(f"_get_live_spot yfinance error: {e}")
    return 0.0


# ── Signal thread — runs every 5 min at candle close, handles entry ──────────

def _run_loop(session: dict, signal_fn, stop_flag: threading.Event, save_session_fn=None):
    instrument = session["instrument"]
    engine: PaperEngine | None = session.get("engine")
    kite   = session.get("kite")
    lot_size = md.LOT_SIZE.get(instrument, 75)

    _log(session, f"Session started | {instrument} | paper={session['paper']} | strategy={session['strategy']}")

    _last_market_closed_log = 0  # throttle "market closed" log to once per 5 min
    _last_wait_log = 0

    while not stop_flag.is_set():
        now          = datetime.datetime.now().time()
        market_open  = datetime.time(9, 15)
        market_close = datetime.time(15, 20)
        no_trade     = datetime.time(15, 0)
        vol_end      = datetime.time(9, 45)

        if not (market_open <= now <= market_close):
            if time.time() - _last_market_closed_log > 300:
                _log(session, f"Market closed | waiting for 09:15 | spot check paused")
                _last_market_closed_log = time.time()
            time.sleep(60)
            continue

        try:
            raw_df = md.fetch_candles_yahoo(instrument)
            closed_raw = md.closed_candles(raw_df, interval="5m")
            df = md.add_indicators(closed_raw)
        except Exception as e:
            _log(session, f"Data fetch error: {e}")
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        if df.empty:
            _log(session, "Empty candle data. Retrying...")
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        latest_candle_ts = df.index[-1]
        spot = float(session.get("last_spot") or df.iloc[-1]["close"])
        session["last_candles"] = df.tail(50).reset_index().to_dict(orient="records")
        session["last_closed_candle"] = str(latest_candle_ts)
        session["last_data_status"] = {
            "latest_closed_candle": str(latest_candle_ts),
            "latest_closed_close": round(float(df.iloc[-1]["close"]), 2),
            "latest_closed_high": round(float(df.iloc[-1]["high"]), 2),
            "latest_closed_low": round(float(df.iloc[-1]["low"]), 2),
            "raw_rows": len(raw_df),
            "closed_rows": len(df),
            "dropped_forming_candles": closed_raw.attrs.get("dropped_forming_candles", 0),
        }

        if engine and session["paper"]:
            _check_closed_candle_exits(session, engine, kite, latest_candle_ts, df.iloc[-1])

        last_processed = session.get("last_signal_candle")
        if last_processed and str(latest_candle_ts) <= str(last_processed):
            if time.time() - _last_wait_log >= 60:
                _log(session, f"Waiting for new closed candle | latest={latest_candle_ts} | dropped_forming={closed_raw.attrs.get('dropped_forming_candles', 0)}")
                _last_wait_log = time.time()
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        # Signal thread only checks SL/Target if monitor thread not running (non-paper).
        if engine and not session["paper"]:
            engine.check_trades(spot)
            session["engine_summary"] = engine.summary()

        if now > no_trade or now < vol_end:
            session["last_signal_candle"] = str(latest_candle_ts)
            _log(session, f"Signal skipped by time filter | candle={latest_candle_ts} | now={now.strftime('%H:%M:%S')}")
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        # Skip new signal if there's already an open trade or pending breakout
        if engine and engine.open_trades:
            session["last_signal_candle"] = str(latest_candle_ts)
            _log(session, f"Open trade active | candle={latest_candle_ts} | spot={spot:.2f} | skipping signal check")
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        if session.get("pending_signal"):
            p = session["pending_signal"]
            session["last_signal_candle"] = str(latest_candle_ts)
            _log(session, f"Pending {p['direction']} breakout@{p['breakout_level']} | candle={latest_candle_ts} | still watching")
            time.sleep(config.SIGNAL_POLL_SECONDS)
            continue

        if session["strategy"] == "8-30 EMA":
            signal, diag = explain_signal_ema(df)
        else:
            signal = signal_fn(df)
            diag = {"strategy": session["strategy"], "reason": "custom strategy", "signal": bool(signal)}
        session["last_signal_diag"] = diag
        session["last_signal_candle"] = str(latest_candle_ts)
        if signal:
            _log(session, _format_signal_log("SIGNAL", diag, signal))
            if signal["entry_type"] == "Retest":
                # Retest: price already at EMA30 — enter immediately at candle close
                _place_entry(session, engine, kite, signal, spot, instrument, lot_size)
            else:
                # Continuation: wait for live breakout of candle high/low
                # Store pending signal — monitor thread will trigger entry on breakout
                session["pending_signal"] = {
                    **signal,
                    "breakout_level": signal["entry"],  # high+buffer (BUY) or low-buffer (SELL)
                    "candle_close":   spot,
                    "set_at":         datetime.datetime.now().isoformat(),
                }
                _log(session, f"PENDING {signal['direction']} | waiting breakout @ {signal['entry']} | spot={spot:.0f}")
        else:
            _log(session, _format_signal_log("No signal", diag, None))

        time.sleep(config.SIGNAL_POLL_SECONDS)

    _log(session, "Session stopped.")


def _format_signal_log(prefix: str, diag: dict, signal: dict | None) -> str:
    parts = [
        f"{prefix} | candle={diag.get('candle_time', 'n/a')}",
        f"dir={diag.get('direction', 'n/a')}",
        f"close={diag.get('close', 'n/a')}",
        f"ema8={diag.get('ema_fast', 'n/a')}",
        f"ema30={diag.get('ema_slow', 'n/a')}",
        f"adx={diag.get('adx', 'n/a')}",
        f"prox={diag.get('ema_slow_proximity_pct', 'n/a')}%",
        f"stretch={diag.get('ema_stretch_pct', 'n/a')}%",
        f"body={diag.get('body_pct', 'n/a')}%",
        f"dom={diag.get('dominance', 'n/a')}",
        f"rej={diag.get('rejection', 'n/a')}",
        f"reason={diag.get('reason', '')}",
    ]
    if signal:
        parts.append(f"entry={signal.get('entry')}")
        parts.append(f"sl={signal.get('sl')}")
        parts.append(f"target={signal.get('target')}")
        parts.append(f"rr=1:{signal.get('rr')}")
    return " | ".join(parts)


def _next_weekly_expiry() -> str:
    today      = datetime.date.today()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + datetime.timedelta(days=days_ahead)).strftime("%y%b%d").upper()


def _get_opt_ltp(kite, symbol: str, spot: float) -> float:
    if kite:
        data = md.fetch_live_option_price(kite, symbol)
        if data and data["ltp"] > 0:
            return data["ltp"]
    return round(spot * 0.015, 2)
