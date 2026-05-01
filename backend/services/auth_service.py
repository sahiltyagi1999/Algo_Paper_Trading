"""
services/auth_service.py
JWT + bcrypt authentication logic.
"""
from datetime import datetime, timezone, timedelta
from functools import wraps

import bcrypt
import jwt
from flask import request, jsonify

import config
from core import database as db


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def make_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def register(username: str, password: str) -> dict:
    if not username or not password:
        return {"error": "username and password required"}
    if len(password) < 6:
        return {"error": "password must be at least 6 characters"}
    if db.find_user(username):
        return {"error": "user already exists"}
    hashed = hash_password(password)
    ok = db.create_user(username, hashed)
    if not ok:
        return {"error": "failed to create user"}
    return {"status": "created", "token": make_token(username)}


def login(username: str, password: str) -> dict:
    if not username or not password:
        return {"error": "username and password required"}
    user = db.find_user(username)
    if not user:
        return {"error": "invalid credentials"}
    if not check_password(password, user["password"]):
        return {"error": "invalid credentials"}
    return {"status": "ok", "token": make_token(username), "username": user["username"]}


def jwt_required(f):
    """Decorator — validates Bearer token on every protected route."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401
        token = auth[7:]
        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "token expired or invalid"}), 401
        return f(*args, **kwargs)
    return wrapper
