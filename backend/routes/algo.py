"""
routes/algo.py
Start/stop/status for the algo trading engine — runs in-process.
"""
from flask import Blueprint, jsonify, request
from services.auth_service import jwt_required
import config
from core import database as db
import core.trading_session as ts

bp = Blueprint("algo", __name__, url_prefix="/api/algo")


def _save_trade(trade: dict):
    db.save_trade(trade)


def _update_trade(trade: dict):
    db.update_trade(trade)


@bp.get("/status")
@jwt_required
def status():
    session = ts.get_active_session()
    if not session:
        return jsonify({"running": False})
    return jsonify({
        "running":    session.get("running", False),
        "session_id": session.get("session_id"),
        "instrument": session.get("instrument"),
        "paper":      session.get("paper"),
        "strategy":   session.get("strategy"),
        "started_at": session.get("started_at"),
        "last_spot":  session.get("last_spot"),
        "last_spot_at": session.get("last_spot_at"),
        "last_closed_candle": session.get("last_closed_candle"),
        "last_risk_candle": session.get("last_risk_candle"),
        "last_signal_diag": session.get("last_signal_diag"),
        "last_data_status": session.get("last_data_status", {}),
        "no_trade_after": config.NO_TRADE_AFTER,
        "square_off_time": config.SQUARE_OFF_TIME,
        "market_close": config.MARKET_CLOSE,
        "summary":    session.get("engine_summary", {}),
    })


@bp.post("/start")
@jwt_required
def start():
    body = request.json or {}
    # Merge with saved settings as defaults
    from services.settings_service import get_settings
    saved = get_settings()
    settings = {**saved, **body}

    if not settings.get("paper_trading", True):
        return jsonify({
            "status": "error",
            "message": "Real-money order placement is not implemented safely in this in-process engine yet. Keep paper_trading=true until Kite entry+broker SL orders are implemented and tested.",
        }), 400

    # Get Kite client whenever available. Paper mode can still use Kite for
    # real option LTP/lot-size; if unavailable, it falls back to simulated LTP.
    kite = None
    try:
        from core.database import load_access_token
        from kiteconnect import KiteConnect
        token_info = load_access_token()
        if token_info:
            kite = KiteConnect(api_key=config.API_KEY)
            kite.set_access_token(token_info[0])
        elif not settings.get("paper_trading", True):
            return jsonify({"status": "error", "message": "No Kite token — connect Kite first"}), 400
    except Exception as e:
        if not settings.get("paper_trading", True):
            return jsonify({"status": "error", "message": f"Kite error: {e}"}), 400

    # Restore today's open trades into engine so monitor thread can track SL/Target
    todays_trades = db.get_todays_trades() if db.is_connected() else []
    open_trades   = [t for t in todays_trades if t.get("status") == "OPEN"]
    closed_today  = [t for t in todays_trades if t.get("status") != "OPEN"]
    restored_pnl  = sum(t.get("pnl", 0) for t in closed_today)

    result = ts.start_session(
        settings,
        kite=kite,
        save_trade_fn=_save_trade if db.is_connected() else None,
        update_trade_fn=_update_trade if db.is_connected() else None,
        open_trades=open_trades,
        restored_pnl=restored_pnl,
    )
    code = 400 if result.get("status") == "error" else 200
    return jsonify(result), code


@bp.post("/stop")
@jwt_required
def stop():
    result = ts.stop_session()
    return jsonify(result)


@bp.post("/squareoff")
@jwt_required
def squareoff():
    result = ts.squareoff_now(reason="MANUAL_SQUAREOFF")
    code = 400 if result.get("status") == "error" else 200
    return jsonify(result), code


@bp.get("/logs")
@jwt_required
def logs():
    session = ts.get_active_session()
    if not session:
        return jsonify({"logs": []})
    return jsonify({"logs": session.get("logs", [])[-200:]})
