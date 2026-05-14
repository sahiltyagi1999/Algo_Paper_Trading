import datetime, uuid, threading
import config


class PaperEngine:
    def __init__(self, session_id, capital, daily_loss_limit, max_trades,
                 on_trade_save=None, on_trade_update=None, restored_trades=None,
                 restored_pnl: float = 0.0):
        self.session_id       = session_id
        self.capital          = capital
        self.starting_capital = capital
        self.daily_loss_limit = daily_loss_limit
        self.max_trades       = max_trades
        self.open_trades:   list[dict] = list(restored_trades or [])
        self.closed_trades: list[dict] = []
        self.daily_pnl   = float(restored_pnl)
        self.trade_count = len(self.open_trades)
        self.loss_count  = 0
        self._save   = on_trade_save   or (lambda t: None)
        self._update = on_trade_update or (lambda t: None)
        self._lock   = threading.Lock()

    def place_order(self, direction, instrument, entry_price, sl, target,
                    option_symbol, opt_ltp, lots, lot_size, entry_type,
                    strategy_name="8-30 EMA", metadata: dict | None = None):
        with self._lock:
            if self.loss_count >= self.max_trades:
                return {"status": "rejected", "reason": f"Max {self.max_trades} losing trades reached — trading stopped for today"}
            if self.daily_pnl <= -abs(self.daily_loss_limit):
                return {"status": "rejected", "reason": "Daily loss limit hit"}
            if lots <= 0 or lot_size <= 0:
                return {"status": "rejected", "reason": "Position size is 0 by risk/capital rules"}

            tid = str(uuid.uuid4())
            trade = {
                "_id":           tid,
                "trade_id":      tid,
                "session_id":    self.session_id,
                "date":          str(datetime.date.today()),
                "time":          datetime.datetime.now().strftime("%H:%M:%S"),
                "entered_at":    datetime.datetime.now().isoformat(),
                "instrument":    instrument,
                "direction":     direction,
                "entry_type":    entry_type,
                "strategy":      strategy_name,
                "option_symbol": option_symbol,
                "symbol":        option_symbol,
                "opt_type":      "CE" if direction == "BUY" else "PE",
                "lots":          lots,
                "qty":           lots * lot_size,
                "entry_spot":    entry_price,
                "sl_spot":       sl,
                "target_spot":   target,
                "entry":         entry_price,
                "sl":            sl,
                "target":        target,
                "opt_ltp_entry": opt_ltp,
                "total_cost":    round(opt_ltp * lots * lot_size, 2),
                "opt_ltp_exit":  None,
                "pnl":           0.0,
                "status":        "OPEN",
                "exit_reason":   None,
                "exit_time":     None,
            }
            if metadata:
                trade.update({k: v for k, v in metadata.items() if v is not None})
            self.open_trades.append(trade)
            self.trade_count += 1
        try:
            self._save(trade)
        except Exception:
            pass
        return {"status": "placed", "trade": trade}

    def check_trades(self, current_spot: float, opt_ltp_fn=None):
        closed_events = []
        with self._lock:
            still_open = []
            for t in self.open_trades:
                hit = self._spot_hit_at_price(t, current_spot)

                # Option LTP-based SL — if option lost 40% of entry value, cut loss
                if not hit and opt_ltp_fn and t.get("opt_ltp_entry"):
                    current_ltp = opt_ltp_fn(t["option_symbol"])
                    if current_ltp > 0:
                        loss_pct = (t["opt_ltp_entry"] - current_ltp) / t["opt_ltp_entry"]
                        if loss_pct >= config.OPT_SL_PCT:
                            hit = "SL"

                if hit:
                    self._close_trade(
                        t, opt_ltp_fn,
                        "TARGET_HIT" if hit == "TARGET" else "SL_HIT",
                        hit,
                        exit_meta={
                            "exit_source": "live_monitor",
                            "spot_exit": round(float(current_spot), 2),
                        },
                    )
                    closed_events.append({"trade_id": t.get("trade_id"), "hit": hit, "source": "live_monitor"})
                else:
                    still_open.append(t)
            self.open_trades = still_open
        return closed_events

    def check_trades_range(self, candle_high: float, candle_low: float, candle_close: float | None = None,
                           candle_time=None, candle_close_time=None, opt_ltp_fn=None):
        """Backup paper exit check using a fully closed candle's high/low range.

        If SL and target both appear inside the same candle, SL wins. That is
        intentionally conservative because 5-min OHLC cannot prove the order
        of touches inside the candle.
        """
        closed_events = []
        with self._lock:
            still_open = []
            for t in self.open_trades:
                if candle_close_time is not None and self._entered_after(t, candle_close_time):
                    still_open.append(t)
                    continue
                hit, both_touched = self._spot_hit_in_range(t, candle_high, candle_low)
                if hit:
                    self._close_trade(
                        t, opt_ltp_fn,
                        "TARGET_HIT" if hit == "TARGET" else "SL_HIT",
                        hit,
                        exit_meta={
                            "exit_source": "closed_candle_range",
                            "exit_candle_time": str(candle_time) if candle_time is not None else None,
                            "exit_candle_close_time": str(candle_close_time) if candle_close_time is not None else None,
                            "exit_candle_high": round(float(candle_high), 2),
                            "exit_candle_low": round(float(candle_low), 2),
                            "spot_exit": round(float(candle_close), 2) if candle_close is not None else None,
                            "both_sl_target_touched": bool(both_touched),
                            "exit_priority": "SL_FIRST" if both_touched else hit,
                        },
                    )
                    closed_events.append({
                        "trade_id": t.get("trade_id"),
                        "hit": hit,
                        "source": "closed_candle_range",
                        "both_touched": bool(both_touched),
                    })
                else:
                    still_open.append(t)
            self.open_trades = still_open
        return closed_events

    def close_all(self, opt_ltp_fn=None, status="CLOSED_EOD", reason="EOD", source="eod_squareoff"):
        with self._lock:
            for t in list(self.open_trades):
                self._close_trade(
                    t, opt_ltp_fn, status, reason,
                    exit_meta={"exit_source": source},
                )
            self.open_trades = []

    def close_trade(self, trade_id: str, opt_ltp_fn=None, exit_ltp: float | None = None,
                    status="MANUAL_CLOSE", reason="MANUAL_CLOSE", source="manual_close"):
        with self._lock:
            still_open = []
            closed_trade = None
            for t in self.open_trades:
                if t.get("trade_id") == trade_id:
                    ltp_fn = (lambda _sym: exit_ltp) if exit_ltp and exit_ltp > 0 else opt_ltp_fn
                    self._close_trade(
                        t, ltp_fn, status, reason,
                        exit_meta={"exit_source": source},
                    )
                    closed_trade = t
                else:
                    still_open.append(t)
            self.open_trades = still_open
        return closed_trade

    def _close_trade(self, t, opt_ltp_fn, status, reason, exit_meta: dict | None = None):
        exit_ltp = opt_ltp_fn(t["option_symbol"]) if opt_ltp_fn else t["opt_ltp_entry"]
        if exit_ltp is None or exit_ltp <= 0:
            exit_ltp = t["opt_ltp_entry"]
        pnl = (exit_ltp - t["opt_ltp_entry"]) * t["qty"]
        updates = {
            "opt_ltp_exit": exit_ltp,
            "exit_price":   exit_ltp,
            "exit_value":   round(exit_ltp * t["qty"], 2),
            "pnl":          round(pnl, 2),
            "status":       status,
            "exit_reason":  reason,
            "exit_time":    datetime.datetime.now().strftime("%H:%M:%S"),
        }
        if exit_meta:
            updates.update({k: v for k, v in exit_meta.items() if v is not None})
        t.update(updates)
        self.daily_pnl += pnl
        self.capital   += pnl
        if pnl < 0:
            self.loss_count += 1
        self.closed_trades.append(t)
        try:
            self._update(t)
        except Exception:
            pass

    @staticmethod
    def _spot_hit_at_price(t: dict, current_spot: float) -> str | None:
        if t["direction"] == "BUY":
            if current_spot >= t["target_spot"]:
                return "TARGET"
            if current_spot <= t["sl_spot"]:
                return "SL"
        else:
            if current_spot <= t["target_spot"]:
                return "TARGET"
            if current_spot >= t["sl_spot"]:
                return "SL"
        return None

    @staticmethod
    def _spot_hit_in_range(t: dict, candle_high: float, candle_low: float) -> tuple[str | None, bool]:
        if t["direction"] == "BUY":
            target_hit = candle_high >= t["target_spot"]
            sl_hit = candle_low <= t["sl_spot"]
        else:
            target_hit = candle_low <= t["target_spot"]
            sl_hit = candle_high >= t["sl_spot"]

        both_touched = target_hit and sl_hit
        if sl_hit:
            return "SL", both_touched
        if target_hit:
            return "TARGET", False
        return None, False

    @staticmethod
    def _entered_after(t: dict, candle_close_time) -> bool:
        entered_at = t.get("entered_at")
        if not entered_at:
            return False
        try:
            entered_dt = datetime.datetime.fromisoformat(str(entered_at))
            if getattr(candle_close_time, "tzinfo", None) is not None and candle_close_time.tzinfo:
                candle_close_time = candle_close_time.astimezone().replace(tzinfo=None)
            if entered_dt.tzinfo:
                entered_dt = entered_dt.astimezone().replace(tzinfo=None)
            return entered_dt > candle_close_time
        except Exception:
            return False

    @staticmethod
    def calculate_lots(capital, opt_entry, opt_sl, lot_size, risk_pct=config.RISK_PCT):
        if opt_entry <= 0 or lot_size <= 0:
            return 0
        risk_per_lot = abs(opt_entry - opt_sl) * lot_size
        if risk_per_lot <= 0:
            return 0
        lots = int((capital * risk_pct) / risk_per_lot)
        return lots if lots >= 1 else 0

    def summary(self) -> dict:
        wins   = [t for t in self.closed_trades if t["pnl"] > 0]
        losses = [t for t in self.closed_trades if t["pnl"] <= 0]
        return {
            "session_id":    self.session_id,
            "date":          str(datetime.date.today()),
            "capital_start": self.starting_capital,
            "capital_now":   round(self.capital, 2),
            "daily_pnl":     round(self.daily_pnl, 2),
            "open_trades":   len(self.open_trades),
            "closed_trades": len(self.closed_trades),
            "wins":          len(wins),
            "losses":        len(losses),
            "loss_count":    self.loss_count,
            "max_losses":    self.max_trades,
            "trading_halted": self.loss_count >= self.max_trades,
            "win_rate":      round(len(wins) / max(len(self.closed_trades), 1) * 100, 1),
        }
