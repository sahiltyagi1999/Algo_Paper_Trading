from datetime import datetime

from flask import Blueprint, jsonify, request
from services.trade_service import (
    get_all_trades, get_todays_trades,
    build_equity_curve, build_summary,
    close_trade_now,
)
from services.auth_service import jwt_required
from core import database as db
import core.trading_session as ts

bp = Blueprint("trades", __name__, url_prefix="/api")


@bp.get("/trades")
@jwt_required
def trades():
    return jsonify(get_all_trades())


@bp.get("/summary")
@jwt_required
def summary():
    return jsonify({
        "all":   build_summary(get_all_trades()),
        "today": build_summary(get_todays_trades()),
    })


@bp.get("/equity")
@jwt_required
def equity():
    return jsonify(build_equity_curve(get_all_trades()))


@bp.get("/todays_equity")
@jwt_required
def todays_equity():
    return jsonify(build_equity_curve(get_todays_trades()))


@bp.get("/daily_history")
@jwt_required
def daily_history():
    return jsonify(db.get_daily_summaries())


@bp.post("/trades/<trade_id>/close")
@jwt_required
def close_trade(trade_id):
    """
    Manually close an OPEN trade at the given exit_price.
    Works for both paper and real trades.
    Body: { "exit_price": 185.5 }   (optional — omit to use last LTP from Kite)
    """
    data       = request.json or {}
    exit_price = data.get("exit_price")
    try:
        parsed_exit = float(exit_price) if exit_price not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid exit_price"}), 400

    active_result = ts.close_trade_now(trade_id, parsed_exit)
    if active_result.get("status") == "closed":
        trade = active_result["trade"]
        return jsonify({
            "status":       "closed",
            "trade_id":     trade_id,
            "symbol":       trade.get("option_symbol") or trade.get("symbol"),
            "exit_price":   trade.get("opt_ltp_exit") or trade.get("exit_price"),
            "pnl":          trade.get("pnl"),
            "mode":         "paper",
            "source":       "active_engine",
        })

    result     = close_trade_now(trade_id, exit_price)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)
