"""
Option Chain — fetches live option prices via Zerodha Kite API.
Uses real ATM option LTP, OI, bid/ask for paper trading.
"""
import logging
from datetime import date, datetime

import config

log = logging.getLogger(__name__)

# Strike gaps per instrument
STRIKE_GAPS = {"NIFTY": 50, "BANKNIFTY": 100}

# Fallback lot sizes (Kite returns real lot size — these are last-resort fallbacks)
_FALLBACK_LOT_SIZES = {"NIFTY": 65, "BANKNIFTY": 15}

# Cached instruments DataFrame to avoid fetching every call (refreshed once per session)
_instruments_cache = None
_instruments_date  = None


def _get_instruments(kite):
    global _instruments_cache, _instruments_date
    today = date.today()
    if _instruments_cache is None or _instruments_date != today:
        try:
            import pandas as pd
            raw = kite.instruments("NFO")
            _instruments_cache = pd.DataFrame(raw)
            _instruments_date  = today
            log.info("NFO instruments refreshed from Kite")
        except Exception as e:
            log.error(f"Failed to fetch NFO instruments: {e}")
            return None
    return _instruments_cache


def get_atm_strike(spot: float, instrument: str) -> int:
    gap = STRIKE_GAPS.get(instrument, 50)
    return round(spot / gap) * gap


def fetch_option_price(instrument: str, spot: float,
                       direction: str, kite=None) -> dict | None:
    """
    Fetch live ATM option price via Kite API.

    direction: "BUY" → CE (call), "SELL" → PE (put)

    Returns dict with:
        symbol      : full option tradingsymbol e.g. NIFTY26APR24500CE
        strike      : ATM strike price
        opt_type    : CE or PE
        ltp         : last traded price (the option premium)
        bid         : best buy price
        ask         : best sell price
        oi          : open interest
        volume      : traded volume today
        expiry      : expiry date (date object)
        lot_size    : lot size for this instrument
        lot_value   : ltp * lot_size (value of 1 lot)
    """
    if kite is None:
        from zerodha_login import get_kite
        kite = get_kite()

    opt_type = "CE" if direction == "BUY" else "PE"
    strike   = get_atm_strike(spot, instrument)

    try:
        df = _get_instruments(kite)
        if df is None:
            return None

        # Filter to this instrument + type
        opts = df[
            (df["name"] == instrument) &
            (df["instrument_type"] == opt_type) &
            (df["strike"] == float(strike))
        ]

        if opts.empty:
            log.warning(f"No {instrument} {opt_type} options found at strike {strike}")
            return None

        today    = date.today()
        expiries = sorted(opts["expiry"].unique())

        # Skip current week expiry if:
        # - today IS expiry day (zero value risk), OR
        # - expiry is within 2 days (theta decay too fast, low liquidity)
        nearest = expiries[0]
        days_to_expiry = (nearest - today).days
        if days_to_expiry <= 1 and len(expiries) > 1:
            log.info(f"Expiry in {days_to_expiry} day(s) ({nearest}) — switching to next: {expiries[1]}")
            nearest = expiries[1]

        row = opts[opts["expiry"] == nearest]
        if row.empty:
            log.warning(f"No option row found for {instrument} {opt_type} {strike} expiry {nearest}")
            return None

        row      = row.iloc[0]
        symbol   = row["tradingsymbol"]
        lot_size = int(row["lot_size"]) or _FALLBACK_LOT_SIZES.get(instrument, 65)
        token    = int(row["instrument_token"])

        # Fetch live quote
        quote_key = f"NFO:{symbol}"
        quotes    = kite.quote([quote_key])
        q         = quotes.get(quote_key, {})

        ltp    = float(q.get("last_price", 0))
        oi     = int(q.get("oi", 0))
        volume = int(q.get("volume", 0))

        buy_depth  = q.get("depth", {}).get("buy",  [])
        sell_depth = q.get("depth", {}).get("sell", [])
        bid = float(buy_depth[0]["price"])  if buy_depth  else ltp
        ask = float(sell_depth[0]["price"]) if sell_depth else ltp

        if ltp <= 0:
            log.warning(f"LTP=0 for {symbol} — option may be illiquid or expired")
            return None

        result = {
            "symbol"   : symbol,
            "strike"   : strike,
            "opt_type" : opt_type,
            "ltp"      : round(ltp, 2),
            "bid"      : round(bid, 2),
            "ask"      : round(ask, 2),
            "oi"       : oi,
            "volume"   : volume,
            "expiry"   : nearest,
            "lot_size" : lot_size,
            "lot_value": round(ltp * lot_size, 2),
        }

        log.info(
            f"Option | {symbol} | LTP={ltp} Bid={bid} Ask={ask} "
            f"OI={oi:,} Vol={volume:,} Lot={lot_size} LotValue=Rs.{ltp*lot_size:.0f}"
        )
        return result

    except Exception as e:
        log.warning(f"Option price fetch failed: {e}")
        return None


def get_option_sl_target(option_price: float, spot_entry: float,
                         spot_sl: float, spot_target: float,
                         direction: str, lot_size: int = 65,
                         instrument: str = "") -> dict:
    """
    Convert spot-based SL/target to option-price-based SL/target.

    Uses ATM delta approximation (delta ≈ 0.5):
      option moves ~0.5 Rs for every 1 Rs move in spot.

    Both CE (BUY) and PE (SELL) are bought options — premium goes up when
    spot moves in our favour, down when against us.
    So SL is always below entry premium, target always above.
    """
    delta       = 0.5
    spot_risk   = abs(spot_entry - spot_sl)
    spot_reward = abs(spot_target - spot_entry)

    opt_sl     = round(option_price - (spot_risk   * delta), 2)
    opt_target = round(option_price + (spot_reward * delta), 2)

    lot      = lot_size or _FALLBACK_LOT_SIZES.get(instrument, 65)
    opt_risk = round((option_price - opt_sl) * lot, 2)

    return {
        "option_entry"    : option_price,
        "option_sl"       : max(opt_sl, 1.0),
        "option_target"   : opt_target,
        "opt_risk_per_lot": opt_risk,
        "lot_size"        : lot,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = fetch_option_price("NIFTY", 24500, "BUY")
    if result:
        print("\nATM Call Option:")
        for k, v in result.items():
            print(f"  {k:12}: {v}")
