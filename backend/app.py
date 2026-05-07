"""
app.py — Flask application factory.
"""
import logging
import os
from datetime import date

from flask import Flask
from flask_cors import CORS

import config
from core import database as db
from routes.trades   import bp as trades_bp
from routes.kite     import bp as kite_bp
from routes.settings import bp as settings_bp
from routes.market   import bp as market_bp
from routes.auth     import bp as auth_bp
from routes.algo     import bp as algo_bp


class MongoLogHandler(logging.Handler):
    """Writes log records to MongoDB logs collection in real-time."""
    # Loggers to skip — too noisy, not useful in UI
    _SKIP = {"werkzeug", "urllib3", "yfinance", "peewee"}

    def emit(self, record):
        if not db.is_connected():
            return
        if record.name.split(".")[0] in self._SKIP:
            return
        try:
            line = self.format(record)
            db.save_log_line(line, str(date.today()))
        except Exception:
            pass


_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_mongo_handler = MongoLogHandler()
_mongo_handler.setFormatter(_fmt)
_mongo_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Attach MongoDB handler to root logger so all loggers feed it
logging.getLogger().addHandler(_mongo_handler)

log = logging.getLogger(__name__)
_STARTED = False


def create_app() -> Flask:
    app = Flask(__name__)

    CORS(app, origins=config.FRONTEND_URL, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(kite_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(algo_bp)

    return app


def _startup():
    global _STARTED
    if _STARTED:
        return
    _STARTED = True
    if config.MONGO_URL:
        ok = db.connect(config.MONGO_URL)
        log.info("MongoDB: connected" if ok else "MongoDB: connection failed")
    else:
        log.warning("MONGO_URL not set — add it to .env")

    if db.is_connected():
        creds = db.load_kite_creds()
        if creds:
            config.API_KEY    = creds.get("api_key",    config.API_KEY)
            config.API_SECRET = creds.get("api_secret", config.API_SECRET)
            log.info(f"Kite creds restored — key: {config.API_KEY[:8]}...")

        if not db.user_exists():
            log.info("No users found — first login will trigger registration screen")


app = create_app()
_startup()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 4200))
    print(f"\n{'='*45}\n  API → http://localhost:{port}\n  Auth: POST /api/auth/login\n{'='*45}\n")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
