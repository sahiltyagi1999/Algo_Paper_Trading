"""
core/database.py — MongoDB connection manager (singleton).
All collections: trades, kite_creds, app_config, logs, daily_summary.
"""
import logging
import re
from datetime import date, datetime

from pymongo import DESCENDING, MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

log = logging.getLogger(__name__)

_client = None
_db     = None


# ── Connection ────────────────────────────────────────────────────────────────

def connect(mongo_url: str = None) -> bool:
    global _client, _db
    import config
    url = mongo_url or config.MONGO_URL
    if not url:
        log.warning("MONGO_URL not set")
        return False
    try:
        _client = MongoClient(url, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[config.DB_NAME]
        _ensure_indexes()
        log.info(f"MongoDB connected → {config.DB_NAME}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        log.error(f"MongoDB connection failed: {e}")
        _client = _db = None
        return False


def is_connected() -> bool:
    return _db is not None


def get_db():
    return _db


def _ensure_indexes():
    _db["trades"].create_index([("date", DESCENDING)])
    _db["trades"].create_index([("trade_id", 1)], unique=True, sparse=True)
    _db["daily_summary"].create_index([("date", 1)], unique=True)
    _db["logs"].create_index([("ts", DESCENDING)])
    _db["logs"].create_index([("log_date", 1)])
    _db["users"].create_index([("username", 1)], unique=True)


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(username: str, hashed_password: str, role: str = "admin") -> bool:
    if _db is None:
        return False
    try:
        _db["users"].insert_one({
            "username":  username.lower().strip(),
            "password":  hashed_password,
            "role":      role,
            "created_at": datetime.utcnow(),
        })
        return True
    except Exception:
        return False


def find_user(username: str) -> dict | None:
    if _db is None:
        return None
    return _db["users"].find_one({"username": username.lower().strip()}, {"_id": 0})


def user_exists() -> bool:
    if _db is None:
        return False
    return bool(_db["users"].count_documents({}, limit=1))


# ── Trades ────────────────────────────────────────────────────────────────────

def save_trade(trade: dict):
    if _db is None:
        return
    doc = {k: v for k, v in trade.items() if k != "_id"}
    try:
        _db["trades"].update_one(
            {"trade_id": doc["trade_id"]},
            {"$setOnInsert": doc},
            upsert=True,
        )
    except Exception as e:
        log.error(f"save_trade: {e}")


def update_trade(trade: dict):
    if _db is None:
        return
    doc = {k: v for k, v in trade.items() if k != "_id"}
    try:
        _db["trades"].update_one(
            {"trade_id": doc["trade_id"]},
            {"$set": doc},
            upsert=True,
        )
    except Exception as e:
        log.error(f"update_trade: {e}")


def get_trades(filters: dict = None, limit: int = 500) -> list[dict]:
    if _db is None:
        return []
    return list(
        _db["trades"]
        .find(filters or {}, {"_id": 0})
        .sort("date", DESCENDING)
        .limit(limit)
    )


def get_all_trades() -> list[dict]:
    return get_trades(limit=500)


def get_todays_trades() -> list[dict]:
    today = str(date.today())
    return get_trades({"date": {"$regex": f"^{re.escape(today)}"}})


# ── Kite credentials ──────────────────────────────────────────────────────────

def save_kite_creds(api_key: str, api_secret: str,
                    access_token: str = "", token_date: str = ""):
    if _db is None:
        return
    _db["kite_creds"].update_one(
        {"_id": "kite"},
        {"$set": {
            "api_key":      api_key,
            "api_secret":   api_secret,
            "access_token": access_token,
            "token_date":   token_date or str(date.today()),
        }},
        upsert=True,
    )


def load_kite_creds() -> dict | None:
    if _db is None:
        return None
    return _db["kite_creds"].find_one({"_id": "kite"}, {"_id": 0})


def load_access_token() -> tuple[str, str] | None:
    """Returns (access_token, token_date) if today's token exists."""
    if _db is None:
        return None
    doc = _db["kite_creds"].find_one({"_id": "kite"}, {"_id": 0})
    if doc and doc.get("token_date") == str(date.today()) and doc.get("access_token"):
        return doc["access_token"], doc["token_date"]
    return None


# ── App config ────────────────────────────────────────────────────────────────

def save_app_config(cfg: dict):
    if _db is None:
        return
    _db["app_config"].update_one(
        {"_id": "main"}, {"$set": cfg}, upsert=True
    )


def load_app_config() -> dict:
    if _db is None:
        return {}
    return _db["app_config"].find_one({"_id": "main"}, {"_id": 0}) or {}


# ── Logs ──────────────────────────────────────────────────────────────────────

def save_log_line(line: str, log_date: str = ""):
    if _db is None:
        return
    line = line.rstrip("\n")
    if not line:
        return
    try:
        _db["logs"].insert_one({
            "ts":       datetime.now(),
            "log_date": log_date or str(date.today()),
            "line":     line,
        })
    except Exception:
        pass


def get_logs(log_date: str = "", limit: int = 500) -> list[str]:
    if _db is None:
        return []
    docs = list(
        _db["logs"]
        .find({"log_date": log_date or str(date.today())}, {"_id": 0, "line": 1})
        .sort("ts", 1)
        .limit(limit)
    )
    return [d["line"] for d in docs]


def import_log_file(path: str, log_date: str) -> int:
    if _db is None:
        return 0
    if _db["logs"].count_documents({"log_date": log_date}, limit=1):
        return 0
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return 0
    docs = []
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        ts = datetime.now()
        try:
            ts = datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f")
        except (ValueError, IndexError):
            pass
        docs.append({"ts": ts, "log_date": log_date, "line": line})
    if docs:
        _db["logs"].insert_many(docs, ordered=False)
    return len(docs)


# ── Daily summary ─────────────────────────────────────────────────────────────

def save_daily_summary(summary: dict):
    if _db is None:
        return
    _db["daily_summary"].update_one(
        {"date": summary.get("date", str(date.today()))},
        {"$set": summary},
        upsert=True,
    )


def get_daily_summaries(limit: int = 30) -> list[dict]:
    if _db is None:
        return []
    return list(
        _db["daily_summary"]
        .find({}, {"_id": 0})
        .sort("date", DESCENDING)
        .limit(limit)
    )


def import_summary_file(path: str) -> bool:
    if _db is None:
        return False
    import json
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    day = data.get("date", "")
    if not day or _db["daily_summary"].count_documents({"date": day}, limit=1):
        return False
    _db["daily_summary"].update_one({"date": day}, {"$set": data}, upsert=True)
    return True
