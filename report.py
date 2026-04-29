"""
Daily Report Generator
Prints trade alerts + end-of-day summary.
Saves daily JSON + CSV. Sends optional WhatsApp alerts.
"""
import json
import logging
import os
from datetime import date, datetime

import requests
import config

log = logging.getLogger(__name__)


def _send_whatsapp(message: str):
    if not config.WHATSAPP_PHONE or not config.WHATSAPP_APIKEY:
        return
    try:
        requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": config.WHATSAPP_PHONE,
                    "text" : message,
                    "apikey": config.WHATSAPP_APIKEY},
            timeout=10,
        )
    except requests.RequestException as e:
        log.warning(f"WhatsApp alert failed: {e}")


def print_trade_alert(trade: dict, action: str):
    direction = trade["direction"]
    opt_type  = trade.get("opt_type", "CE" if direction == "BUY" else "PE")
    call_put  = "CALL (CE)" if opt_type == "CE" else "PUT  (PE)"
    action_str = f"{call_put} — {'BUY' if direction == 'BUY' else 'BUY'}"  # we always BUY the option

    if action == "ENTRY":
        lots      = trade.get("lots", "—")
        spot      = trade.get("spot_entry", "—")
        cost      = trade.get("total_cost", trade["entry"] * trade["qty"])
        lot_size  = trade["qty"] // lots if isinstance(lots, int) and lots > 0 else "?"
        ltp       = trade.get("ltp_at_entry", trade["entry"])
        bid       = trade.get("bid_at_entry", "—")
        ask       = trade.get("ask_at_entry", "—")
        msg = (
            f"\n{'='*50}\n"
            f"  PAPER TRADE #{trade['id']} — ENTRY\n"
            f"  Action       : {action_str}\n"
            f"  Symbol       : {trade['symbol']}\n"
            f"  Signal Type  : {trade['entry_type']}\n"
            f"  Nifty Spot   : Rs.{spot}\n"
            f"  Option LTP   : Rs.{ltp}  (Bid:{bid} / Ask:{ask})\n"
            f"  Option SL    : Rs.{trade['sl']}\n"
            f"  Option Target: Rs.{trade['target']}  (1:{trade['rr']})\n"
            f"  Lots x Size  : {lots} lots x {lot_size} = {trade['qty']} qty\n"
            f"  Total Cost   : Rs.{cost:,.2f}\n"
            f"  Time         : {trade['entry_time']}\n"
            f"{'='*50}"
        )
    else:
        result     = trade["status"]
        outcome    = "WIN — TARGET HIT" if result == "TARGET_HIT" else "LOSS — SL HIT"
        pnl        = trade["pnl"]
        pnl_str    = f"+Rs.{pnl:.2f}" if pnl >= 0 else f"-Rs.{abs(pnl):.2f}"
        cost       = trade.get("total_cost", "—")
        exit_val   = trade.get("exit_value", "—")
        msg = (
            f"\n{'='*50}\n"
            f"  {outcome} — Trade #{trade['id']}\n"
            f"  Bought For  : Rs.{cost:,.2f}  (total cost)\n"
            f"  Sold For    : Rs.{exit_val:,.2f}  (total exit value)\n"
            f"  Exit Price  : Rs.{trade['exit_price']}  per unit\n"
            f"  PnL         : {pnl_str}\n"
            f"  Exit Time   : {trade['exit_time']}\n"
            f"{'='*50}"
        )

    print(msg)
    log.info(msg.replace("\n", " ").strip())
    _send_whatsapp(msg)


def print_daily_report(summary: dict, vix: float | None = None,
                       oi_levels: dict | None = None,
                       all_trades: list | None = None):
    pnl       = summary["daily_pnl"]
    sign      = "+" if pnl >= 0 else ""
    today_str = date.today().strftime("%d %b %Y")
    today_iso = date.today().isoformat()

    msg = (
        f"\n{'='*50}\n"
        f"  PAPER TRADING REPORT — {today_str}\n"
        f"{'='*50}\n"
        f"  Instrument  : {config.INSTRUMENT}\n"
        f"  Capital     : Rs.{config.CAPITAL:,.0f}\n"
        f"  Total Trades: {summary['total_trades']}\n"
        f"  Wins        : {summary['wins']}\n"
        f"  Losses      : {summary['losses']}\n"
        f"  Win Rate    : {summary['win_rate']}%\n"
        f"  Daily PnL   : {sign}Rs.{pnl:,.2f}\n"
        f"  Equity Now  : Rs.{summary['capital']:,.2f}\n"
        f"{'='*50}\n"
        f"  Daily log   : logs/algo_{today_iso}.log\n"
        f"  Trades CSV  : {config.REPORT_FILE}\n"
        f"  Summary JSON: logs/summary_{today_iso}.json\n"
        f"{'='*50}"
    )

    print(msg)
    log.info(msg.replace("\n", " ").strip())
    _send_whatsapp(msg)
    _save_daily_summary(summary, vix, oi_levels, today_iso, all_trades or [])


def _save_daily_summary(summary: dict, vix: float | None,
                        oi_levels: dict | None, today_iso: str,
                        all_trades: list):
    os.makedirs("logs", exist_ok=True)
    path = f"logs/summary_{today_iso}.json"

    trade_log = []
    for t in all_trades:
        trade_log.append({
            "id"             : t.get("id"),
            "symbol"         : t.get("symbol"),
            "direction"      : t.get("direction"),
            "entry_type"     : t.get("entry_type"),
            "opt_type"       : t.get("opt_type"),
            "lots"           : t.get("lots"),
            "qty"            : t.get("qty"),
            "spot_entry"     : t.get("spot_entry"),
            "spot_sl"        : t.get("spot_sl"),
            "spot_target"    : t.get("spot_target"),
            "option_entry"   : t.get("entry"),
            "option_sl"      : t.get("sl"),
            "option_target"  : t.get("target"),
            "ltp_at_entry"   : t.get("ltp_at_entry"),
            "bid_at_entry"   : t.get("bid_at_entry"),
            "ask_at_entry"   : t.get("ask_at_entry"),
            "oi_at_entry"    : t.get("oi_at_entry"),
            "volume_at_entry": t.get("volume_at_entry"),
            "total_cost"     : t.get("total_cost"),
            "status"         : t.get("status"),
            "pnl"            : t.get("pnl"),
            "exit_price"     : t.get("exit_price"),
            "exit_value"     : t.get("exit_value"),
            "entry_time"     : t.get("entry_time"),
            "exit_time"      : t.get("exit_time"),
        })

    data = {
        "date"          : today_iso,
        "saved_at"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "instrument"    : config.INSTRUMENT,
        "capital_start" : config.CAPITAL,
        "capital_end"   : summary["capital"],
        "daily_pnl"     : summary["daily_pnl"],
        "total_trades"  : summary["total_trades"],
        "wins"          : summary["wins"],
        "losses"        : summary["losses"],
        "win_rate"      : summary["win_rate"],
        "open_trades"   : summary["open_trades"],
        "vix"           : vix,
        "oi_support"    : oi_levels.get("support")    if oi_levels else None,
        "oi_resistance" : oi_levels.get("resistance") if oi_levels else None,
        "oi_bias"       : oi_levels.get("bias")       if oi_levels else None,
        "pcr"           : oi_levels.get("pcr")        if oi_levels else None,
        "trades"        : trade_log,
    }
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        log.info(f"Daily summary saved: {path}")
    except OSError as e:
        log.error(f"Failed to save daily summary: {e}")
