from flask import Blueprint, jsonify, request
from services.auth_service import login

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login_route():
    data = request.json or {}
    result = login(data.get("username", "").strip(), data.get("password", ""))
    if "error" in result:
        return jsonify(result), 401
    return jsonify(result)
