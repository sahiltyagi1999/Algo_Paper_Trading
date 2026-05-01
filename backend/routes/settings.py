from flask import Blueprint, jsonify, request
from services.settings_service import get_settings, save_settings
from services.auth_service import jwt_required
from core import database as db
import config

bp = Blueprint("settings", __name__, url_prefix="/api")


@bp.get("/settings")
@jwt_required
def settings_get():
    return jsonify(get_settings())


@bp.post("/settings")
@jwt_required
def settings_post():
    return jsonify(save_settings(request.json or {}))


@bp.post("/mongo/connect")
@jwt_required
def mongo_connect():
    url = (request.json or {}).get("mongo_url", "").strip()
    if not url:
        return jsonify({"error": "mongo_url required"}), 400
    ok = db.connect(url)
    if ok:
        config.MONGO_URL = url
        return jsonify({"status": "connected", "db": config.DB_NAME})
    return jsonify({"error": "Connection failed — check URL and network"}), 400


@bp.get("/mongo/status")
@jwt_required
def mongo_status():
    return jsonify({
        "connected": db.is_connected(),
        "db":        config.DB_NAME if db.is_connected() else None,
    })
