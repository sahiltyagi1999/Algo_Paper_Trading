"""
services/trade_service.py
Business logic for trades, equity curves, daily summaries, and manual close.
All data comes from MongoDB.
"""
import logging
from datetime import datetime

import config
from core import database as db

log = logging.getLogger(__name__)


def get_all_trades() -> list[dict]:
    return db.get_all_trades()


def get_todays_trades() -> list[dict]:
    return db.get_todays_trades()


def build_equity_curve(trades: list[dict]) -> list[dict]:
    equity = float(config.CAPITAL)
    curve  = [{"x": "Start", "y": equity}]
    for t in trades:
        equity += float(t.get("pnl") or 0)
        curve.append({"x": str(t.get("date", ""))[:16], "y": round(equity, 2)})
    return curve


def build_summary(trades: list[dict]) -> dict:
    closed    = [t for t in trades if t.get("status") not in ("OPEN", "")]
    wins      = [t for t in closed if t.get("status") == "TARGET_HIT"]
    losses    = [t for t in closed if t.get("status") == "SL_HIT"]
    total_pnl = sum(float(t.get("pnl") or 0) for t in closed)
    win_rate  = round(len(wins) / len(closed) * 100, 1) if closed else 0.0
    return {
        "total_trades": len(closed),
        "wins":         len(wins),
        "losses":       len(losses),
        "win_rate":     win_rate,
        "total_pnl":    round(total_pnl, 2),
        "capital":      float(config.CAPITAL),
        "profit_vault": float(config.PROFIT_VAULT),
        "total_wealth": round(float(config.CAPITAL) + float(config.PROFIT_VAULT), 2),
        "open_trades":  len([t for t in trades if t.get("status") == "OPEN"]),
    }


def close_trade_now(trade_id: str, exit_price: float | None = None) -> dict:
    """
    Manually close an OPEN trade.
    - Fetches live LTP from Kite if exit_price not provided.
    - Works for both paper and real mode.
    - For real mode: also places a market sell order on Kite.
    """
    if not db.is_connected():
        return {"error": "MongoDB not connected"}

    # Find the trade
    trades = db.get_trades({"trade_id": trade_id})
    if not trades:
        return {"error": "Trade not found"}
    trade = trades[0]

    if trade.get("status") != "OPEN":
        return {"error": f"Trade is already closed (status: {trade['status']})"}

    symbol = trade.get("symbol", "")
    qty    = int(trade.get("qty", 0))
    entry  = float(trade.get("entry", 0))

    # ── Get exit price ────────────────────────────────────────────────────────
    if exit_price is None:
        exit_price = _fetch_ltp(symbol)
        if exit_price is None:
            return {"error": "Could not fetch live price — please enter exit price manually"}

    exit_price = float(exit_price)
    pnl        = round((exit_price - entry) * qty, 2)
    exit_value = round(exit_price * qty, 2)
    exit_time  = datetime.now().strftime("%H:%M:%S")

    # ── Real mode: place market order on Kite ────────────────────────────────
    kite_order_id = None
    if not config.PAPER_TRADING and symbol:
        kite_order_id = _place_kite_exit(symbol, qty)

    # ── Update MongoDB ────────────────────────────────────────────────────────
    updated = {
        **trade,
        "status":     "MANUAL_CLOSE",
        "exit_price": str(exit_price),
        "exit_value": str(exit_value),
        "exit_time":  exit_time,
        "pnl":        str(pnl),
    }
    db.update_trade(updated)
    log.info(f"Manual close: {symbol} @ {exit_price} | PnL: {pnl} | order_id: {kite_order_id}")

    return {
        "status":       "closed",
        "trade_id":     trade_id,
        "symbol":       symbol,
        "exit_price":   exit_price,
        "pnl":          pnl,
        "kite_order_id": kite_order_id,
        "mode":         "paper" if config.PAPER_TRADING else "real",
    }


def _fetch_ltp(symbol: str) -> float | None:
    """Try to get live LTP from Kite for the option symbol."""
    try:
        from core.database import load_access_token
        import config as cfg
        from kiteconnect import KiteConnect
        token_info = load_access_token()
        if not token_info:
            return None
        kite = KiteConnect(api_key=cfg.API_KEY)
        kite.set_access_token(token_info[0])
        quote = kite.quote([f"NFO:{symbol}"])
        return float(quote[f"NFO:{symbol}"]["last_price"])
    except Exception as e:
        log.warning(f"LTP fetch failed for {symbol}: {e}")
        return None


def _place_kite_exit(symbol: str, qty: int) -> str | None:
    """Place a market SELL order on Kite to exit the position."""
    try:
        from core.database import load_access_token
        import config as cfg
        from kiteconnect import KiteConnect
        token_info = load_access_token()
        if not token_info:
            log.warning("No access token — cannot place Kite exit order")
            return None
        kite = KiteConnect(api_key=cfg.API_KEY)
        kite.set_access_token(token_info[0])
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=qty,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS,
        )
        log.info(f"Kite exit order placed: {order_id}")
        return str(order_id)
    except Exception as e:
        log.error(f"Kite exit order failed: {e}")
        return None
