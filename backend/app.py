"""
app.py — Flask application factory.
"""
import logging
import os

from flask import Flask
from flask_cors import CORS

import config
from core import database as db
from routes.trades   import bp as trades_bp
from routes.kite     import bp as kite_bp
from routes.settings import bp as settings_bp
from routes.market   import bp as market_bp
from routes.auth     import bp as auth_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    CORS(app, origins=config.FRONTEND_URL, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(kite_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(market_bp)

    return app


def _startup():
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

if __name__ == "__main__":
    _startup()
    port = int(os.getenv("PORT", 4200))
    print(f"\n{'='*45}\n  API → http://localhost:{port}\n  Auth: POST /api/auth/login\n{'='*45}\n")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
