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
    "square_off_time",
}


def _compute_daily_loss(capital, risk_pct, max_trades):
    return round(float(capital) * float(risk_pct) * int(max_trades), 2)


def get_settings() -> dict:
    cfg = db.load_app_config()
    capital    = cfg.get("capital",        config.CAPITAL)
    risk_pct   = cfg.get("risk_pct",       config.RISK_PCT)
    max_trades = cfg.get("max_trades_day", config.MAX_TRADES_DAY)
    return {
        "instrument":       cfg.get("instrument",    config.INSTRUMENT),
        "paper_trading":    cfg.get("paper_trading", config.PAPER_TRADING),
        "capital":          capital,
        "profit_vault":     cfg.get("profit_vault",  config.PROFIT_VAULT),
        "daily_loss_limit": _compute_daily_loss(capital, risk_pct, max_trades),
        "max_trades_day":   max_trades,
        "risk_pct":         risk_pct,
        "ema_fast":         cfg.get("ema_fast",       config.EMA_FAST),
        "ema_slow":         cfg.get("ema_slow",       config.EMA_SLOW),
        "adx_threshold":    cfg.get("adx_threshold",  config.ADX_THRESHOLD),
        "sl_buffer":        cfg.get("sl_buffer",      config.SL_BUFFER),
        "oi_buffer":        cfg.get("oi_buffer",      config.OI_BUFFER),
        "square_off_time":  cfg.get("square_off_time", config.SQUARE_OFF_TIME),
        "mongo_connected":  db.is_connected(),
        "kite_api_key":     config.API_KEY,
    }


def save_settings(data: dict) -> dict:
    cfg = {k: v for k, v in data.items() if k in _ALLOWED}
    # Apply to live config immediately
    for k, v in cfg.items():
        attr = k.upper()
        if hasattr(config, attr):
            if attr == "SQUARE_OFF_TIME":
                if not _valid_hhmm(v):
                    return {"error": f"Invalid value for {k}: {v!r}. Use HH:MM, e.g. 15:15"}
                setattr(config, attr, str(v))
                continue
            try:
                setattr(config, attr, type(getattr(config, attr))(v))
            except (ValueError, TypeError):
                return {"error": f"Invalid value for {k}: {v!r}"}
    # Always recompute daily_loss_limit from current values
    existing = db.load_app_config()
    capital    = cfg.get("capital",        existing.get("capital",        config.CAPITAL))
    risk_pct   = cfg.get("risk_pct",       existing.get("risk_pct",       config.RISK_PCT))
    max_trades = cfg.get("max_trades_day", existing.get("max_trades_day", config.MAX_TRADES_DAY))
    cfg["daily_loss_limit"] = _compute_daily_loss(capital, risk_pct, max_trades)
    config.DAILY_LOSS_LIMIT = cfg["daily_loss_limit"]
    db.save_app_config(cfg)
    return {"status": "saved"}


def _valid_hhmm(value) -> bool:
    try:
        hour, minute = str(value).split(":", 1)
        hour = int(hour)
        minute = int(minute)
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except Exception:
        return False
