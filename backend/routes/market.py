from flask import Blueprint, jsonify, request
from services.market_service import get_vix, get_oi, get_candles, get_algo_status, get_logs
from services.auth_service import jwt_required

bp = Blueprint("market", __name__, url_prefix="/api")


@bp.get("/vix")
@jwt_required
def vix():
    return jsonify(get_vix())


@bp.get("/oi")
@jwt_required
def oi():
    return jsonify(get_oi())


@bp.get("/candles")
@jwt_required
def candles():
    return jsonify(get_candles())


@bp.get("/status")
@jwt_required
def status():
    return jsonify(get_algo_status())


@bp.get("/logs")
@jwt_required
def logs():
    log_date = request.args.get("date", "")
    try:
        limit = int(request.args.get("limit", 300))
    except (ValueError, TypeError):
        limit = 300
    return jsonify(get_logs(log_date, limit))
