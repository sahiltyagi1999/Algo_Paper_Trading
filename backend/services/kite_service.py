"""
services/kite_service.py
All Zerodha Kite Connect business logic: login URL, token generation, status.
Access token is saved only to MongoDB — no local file dependency.
"""
from datetime import date

import config
from core import database as db


def has_env_creds() -> bool:
    return bool(config.API_KEY and config.API_SECRET)


def get_login_url(api_key: str = "", api_secret: str = "") -> dict:
    key    = api_key    or config.API_KEY
    secret = api_secret or config.API_SECRET
    if not key or not secret:
        return {"error": "api_key and api_secret are required"}
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=key)
        config.API_KEY    = key
        config.API_SECRET = secret
        db.save_kite_creds(key, secret)
        return {"login_url": kite.login_url()}
    except Exception as e:
        return {"error": str(e)}


def generate_token(request_token: str, api_key: str = "", api_secret: str = "") -> dict:
    key    = api_key    or config.API_KEY
    secret = api_secret or config.API_SECRET
    if not all([request_token, key, secret]):
        return {"error": "request_token, api_key, and api_secret are all required"}
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=key)
        sess = kite.generate_session(request_token, api_secret=secret)
        access_token = sess["access_token"]
        db.save_kite_creds(key, secret, access_token, str(date.today()))
        config.API_KEY    = key
        config.API_SECRET = secret
        return {"status": "connected", "user": sess.get("user_name", "")}
    except Exception as e:
        return {"error": str(e)}


def get_status() -> dict:
    base = {"has_env_creds": has_env_creds()}
    token_info = db.load_access_token()
    if token_info:
        return {**base, "connected": True, "date": token_info[1], "source": "mongodb"}
    return {**base, "connected": False}
