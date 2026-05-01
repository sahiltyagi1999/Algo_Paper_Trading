from flask import Blueprint, jsonify, request
from services.kite_service import get_login_url, generate_token, get_status
from services.auth_service import jwt_required

bp = Blueprint("kite", __name__, url_prefix="/api/kite")


@bp.post("/login-url")
@jwt_required
def login_url():
    data   = request.json or {}
    result = get_login_url(
        data.get("api_key",    "").strip(),
        data.get("api_secret", "").strip(),
    )
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bp.post("/generate-token")
@jwt_required
def generate_token_route():
    data   = request.json or {}
    result = generate_token(
        data.get("request_token", "").strip(),
        data.get("api_key",       "").strip(),
        data.get("api_secret",    "").strip(),
    )
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@bp.get("/status")
@jwt_required
def status():
    return jsonify(get_status())
