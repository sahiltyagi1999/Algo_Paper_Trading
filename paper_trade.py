"""
Paper Trading Engine
Simulates trades internally — no real orders sent to Zerodha.
All keys are consistently lowercase throughout.
"""
import csv
import logging
import os
from datetime import datetime

import config

# Injected by algo_trader at startup so engine can fetch live option prices
_kite = None

def set_kite(kite):
    global _kite
    _kite = kite

def _fetch_live_option_price(symbol: str) -> float | None:
    """Fetch current LTP for an option symbol via Kite. Returns None on failure."""
    if _kite is None:
        return None
    try:
        quotes = _kite.quote([f"NFO:{symbol}"])
        ltp = float(quotes[f"NFO:{symbol}"]["last_price"])
        return ltp if ltp > 0 else None
    except Exception as e:
        log_ref = logging.getLogger(__name__)
        log_ref.warning(f"Live price fetch failed for {symbol}: {e}")
        return None

log = logging.getLogger(__name__)


class PaperTradeEngine:
    def __init__(self):
        self.capital       = float(config.CAPITAL)
        self.open_trades   = []
        self.closed_trades = []
        self.daily_pnl     = 0.0
        self.trade_count   = 0
        os.makedirs(os.path.dirname(config.REPORT_FILE), exist_ok=True)

    # ── Place Order ────────────────────────────────────────────────────────────

    def place_order(self, direction, entry, sl, target, rr,
                    entry_type, symbol, qty) -> tuple:
        if self.trade_count >= config.MAX_TRADES_DAY:
            return None, "MAX_TRADES_REACHED"
        if self.daily_pnl <= -config.DAILY_LOSS_LIMIT:
            return None, "DAILY_LOSS_LIMIT_HIT"

        self.trade_count += 1
        trade = {
            "id"             : self.trade_count,
            "symbol"         : symbol,
            "direction"      : direction,
            "entry_type"     : entry_type,
            "entry"          : round(entry, 2),
            "sl"             : round(sl, 2),
            "target"         : round(target, 2),
            "rr"             : rr,
            "qty"            : qty,
            "lots"           : "",          # filled by caller
            "opt_type"       : "",          # CE or PE — filled by caller
            "ltp_at_entry"   : "",          # option LTP when entered — filled by caller
            "bid_at_entry"   : "",          # bid price at entry — filled by caller
            "ask_at_entry"   : "",          # ask price at entry — filled by caller
            "oi_at_entry"    : "",          # open interest at entry — filled by caller
            "volume_at_entry": "",          # volume at entry — filled by caller
            "spot_entry"     : "",          # nifty spot at entry — filled by caller
            "spot_sl"        : "",          # spot-level SL — filled by caller
            "spot_target"    : "",          # spot-level target — filled by caller
            "total_cost"     : round(entry * qty, 2),
            "status"         : "OPEN",
            "pnl"            : 0.0,
            "entry_time"     : datetime.now().strftime("%H:%M:%S"),
            "exit_time"      : None,
            "exit_price"     : None,
            "exit_value"     : None,
            "date"           : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.open_trades.append(trade)
        log.info(f"PAPER ORDER #{trade['id']} | {direction} {symbol} | "
                 f"Entry={entry} SL={sl} Target={target} RR=1:{rr}")
        return trade, "ORDER_PLACED"

    # ── Check Trades Against Current Candle ───────────────────────────────────

    def check_trades(self, candle_high, candle_low, current_price) -> list:
        closed_now = []
        for trade in list(self.open_trades):
            result, exit_price = self._check_single(trade, candle_high, candle_low)
            if result:
                self._close_trade(trade, result, exit_price)
                closed_now.append(trade)
        return closed_now

    def _check_single(self, trade, high, low) -> tuple:
        # Spot candle high/low used to detect trigger.
        # Exit price = real live option LTP at that moment (fetched from Kite).
        spot_sl  = trade.get("spot_sl",  trade["sl"])
        spot_tgt = trade.get("spot_target", trade["target"])
        triggered = None
        if trade["direction"] == "BUY":
            if low <= spot_sl:
                triggered = "SL_HIT"
            elif high >= spot_tgt:
                triggered = "TARGET_HIT"
        else:
            if high >= spot_sl:
                triggered = "SL_HIT"
            elif low <= spot_tgt:
                triggered = "TARGET_HIT"

        if triggered:
            # Fetch real live option price at this moment
            live_ltp = _fetch_live_option_price(trade["symbol"])
            if live_ltp:
                return triggered, live_ltp
            # Fallback to stored option SL/target only if Kite fetch fails
            fallback = trade["sl"] if triggered == "SL_HIT" else trade["target"]
            log.warning(f"Live price unavailable for {trade['symbol']} — using stored option level {fallback}")
            return triggered, fallback

        return None, None

    def _close_trade(self, trade, result, exit_price):
        pnl = (exit_price - trade["entry"]) * trade["qty"]

        trade["status"]     = result
        trade["pnl"]        = round(pnl, 2)
        trade["exit_price"] = round(exit_price, 2)
        trade["exit_value"] = round(exit_price * trade["qty"], 2)
        trade["exit_time"]  = datetime.now().strftime("%H:%M:%S")

        self.daily_pnl += pnl
        self.capital   += pnl
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)
        self._save_trade(trade)

        log.info(f"TRADE CLOSED #{trade['id']} | {result} | "
                 f"OptExit={exit_price} PnL={pnl:+.2f} DayPnL={self.daily_pnl:+.2f}")

    # ── Force Close All at Market End ─────────────────────────────────────────

    def close_all(self, spot_close: float):
        """Close open trades at EOD using real live option price from Kite."""
        for trade in list(self.open_trades):
            # Always try real price first
            opt_exit = _fetch_live_option_price(trade["symbol"])
            if opt_exit is None:
                # Only if Kite is completely unavailable, use delta estimate and flag it
                spot_entry = trade.get("spot_entry", 0)
                if spot_entry and spot_entry > 0:
                    spot_move = spot_close - spot_entry
                    opt_exit  = trade["entry"] + (spot_move * 0.5 if trade["direction"] == "BUY" else -spot_move * 0.5)
                    opt_exit  = max(round(opt_exit, 2), 0.05)
                    log.warning(f"EOD close #{trade['id']}: Kite unavailable, using delta estimate {opt_exit}")
                else:
                    opt_exit = trade["entry"]
                    log.warning(f"EOD close #{trade['id']}: no data at all — exiting flat at entry")

            pnl = (opt_exit - trade["entry"]) * trade["qty"]

            trade["status"]     = "CLOSED_EOD"
            trade["pnl"]        = round(pnl, 2)
            trade["exit_price"] = round(opt_exit, 2)
            trade["exit_value"] = round(opt_exit * trade["qty"], 2)
            trade["exit_time"]  = datetime.now().strftime("%H:%M:%S")

            self.daily_pnl += pnl
            self.capital   += pnl
            self.closed_trades.append(trade)
            self._save_trade(trade)

        self.open_trades.clear()

    # ── Persist Trade to CSV ──────────────────────────────────────────────────

    def _save_trade(self, trade):
        fields = [
            "id", "date", "symbol", "direction", "entry_type",
            "lots", "opt_type", "qty",
            "spot_entry", "spot_sl", "spot_target",
            "entry", "sl", "target", "rr",
            "ltp_at_entry", "bid_at_entry", "ask_at_entry",
            "oi_at_entry", "volume_at_entry",
            "total_cost",
            "status", "pnl", "entry_time", "exit_time", "exit_price", "exit_value",
        ]
        file_exists = os.path.exists(config.REPORT_FILE)
        try:
            with open(config.REPORT_FILE, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                if not file_exists:
                    writer.writeheader()
                writer.writerow({k: trade.get(k, "") for k in fields})
        except OSError as e:
            log.error(f"Failed to save trade #{trade['id']}: {e}")

    # ── Daily Reset (call at 9:15 AM each new trading day) ───────────────────

    def reset_daily(self):
        self.daily_pnl   = 0.0
        self.trade_count = 0
        self.open_trades.clear()
        log.info("Daily counters reset — new trading day started")

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        closed   = [t for t in self.closed_trades if t["status"] != "OPEN"]
        wins     = [t for t in closed if t["status"] == "TARGET_HIT"]
        losses   = [t for t in closed if t["status"] == "SL_HIT"]
        win_rate = round(len(wins) / len(closed) * 100, 1) if closed else 0.0
        return {
            "total_trades": len(closed),
            "wins"        : len(wins),
            "losses"      : len(losses),
            "win_rate"    : win_rate,
            "daily_pnl"   : round(self.daily_pnl, 2),
            "capital"     : round(self.capital, 2),
            "open_trades" : len(self.open_trades),
        }
