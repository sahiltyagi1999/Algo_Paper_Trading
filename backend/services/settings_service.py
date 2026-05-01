"""
services/settings_service.py
Read and write app config. Merges DB overrides with config.py defaults.
"""
import config
from core import database as db

_ALLOWED = {
    "instrument", "paper_trading", "capital", "profit_vault",
    "daily_loss_limit", "max_trades_day", "risk_pct",
    "ema_fast", "ema_slow", "adx_threshold", "sl_buffer", "oi_buffer",
}


def get_settings() -> dict:
    cfg = db.load_app_config()
    return {
        "instrument":       cfg.get("instrument",       config.INSTRUMENT),
        "paper_trading":    cfg.get("paper_trading",    config.PAPER_TRADING),
        "capital":          cfg.get("capital",          config.CAPITAL),
        "profit_vault":     cfg.get("profit_vault",     config.PROFIT_VAULT),
        "daily_loss_limit": cfg.get("daily_loss_limit", config.DAILY_LOSS_LIMIT),
        "max_trades_day":   cfg.get("max_trades_day",   config.MAX_TRADES_DAY),
        "risk_pct":         cfg.get("risk_pct",         config.RISK_PCT),
        "ema_fast":         cfg.get("ema_fast",         config.EMA_FAST),
        "ema_slow":         cfg.get("ema_slow",         config.EMA_SLOW),
        "adx_threshold":    cfg.get("adx_threshold",    config.ADX_THRESHOLD),
        "sl_buffer":        cfg.get("sl_buffer",        config.SL_BUFFER),
        "oi_buffer":        cfg.get("oi_buffer",        config.OI_BUFFER),
        "mongo_connected":  db.is_connected(),
        "kite_api_key":     config.API_KEY,
    }


def save_settings(data: dict) -> dict:
    cfg = {k: v for k, v in data.items() if k in _ALLOWED}
    # Apply to live config immediately
    for k, v in cfg.items():
        attr = k.upper()
        if hasattr(config, attr):
            setattr(config, attr, type(getattr(config, attr))(v))
    db.save_app_config(cfg)
    return {"status": "saved"}
