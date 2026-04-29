"""
OI Data Fetcher — fetches live Open Interest from Zerodha Kite API.
Calculates support (max PE OI), resistance (max CE OI), PCR.
Uses the same NFO instruments + quote calls as option_chain.py.
"""
import logging
from datetime import date

import config

log = logging.getLogger(__name__)

# How many strikes above/below ATM to scan for max OI
_SCAN_STRIKES = 10


def get_oi_levels(instrument: str = "NIFTY", kite=None, spot: float = 0) -> dict | None:
    """
    Fetch OI across strikes near current spot price via Kite API.
    Returns support (highest PE OI strike), resistance (highest CE OI strike), PCR, bias.
    Returns None if Kite is unavailable — algo continues without OI filter.
    """
    if kite is None:
        try:
            from zerodha_login import get_kite
            kite = get_kite()
        except Exception:
            log.warning("OI: Kite not available — skipping OI levels")
            return None

    try:
        from option_chain import _get_instruments, get_atm_strike, STRIKE_GAPS
        import pandas as pd

        df = _get_instruments(kite)
        if df is None:
            return None

        gap = STRIKE_GAPS.get(instrument, 50)

        # Filter to nearest expiry CE and PE
        today    = date.today()
        opts     = df[df["name"] == instrument].copy()
        expiries = sorted(opts["expiry"].unique())
        if not len(expiries):
            return None

        nearest = expiries[0]
        if (nearest - today).days <= 1 and len(expiries) > 1:
            log.info(f"OI: expiry {nearest} too close — using {expiries[1]}")
            nearest = expiries[1]

        ce_opts = opts[(opts["instrument_type"] == "CE") & (opts["expiry"] == nearest)]
        pe_opts = opts[(opts["instrument_type"] == "PE") & (opts["expiry"] == nearest)]

        all_strikes = sorted(set(ce_opts["strike"].tolist()) & set(pe_opts["strike"].tolist()))
        if not all_strikes:
            return None

        # Scan around current spot price, not list midpoint
        if spot > 0:
            atm = get_atm_strike(spot, instrument)
        else:
            atm = all_strikes[len(all_strikes) // 2]  # fallback if no spot given

        # Pick strikes within _SCAN_STRIKES gaps of ATM
        strikes = [s for s in all_strikes if abs(s - atm) <= _SCAN_STRIKES * gap]
        if not strikes:
            strikes = all_strikes  # fallback: use all

        # Build list of quote keys
        ce_rows = ce_opts[ce_opts["strike"].isin(strikes)]
        pe_rows = pe_opts[pe_opts["strike"].isin(strikes)]

        symbols = (
            [f"NFO:{s}" for s in ce_rows["tradingsymbol"].tolist()] +
            [f"NFO:{s}" for s in pe_rows["tradingsymbol"].tolist()]
        )
        if not symbols:
            return None

        # Kite quote allows up to 500 instruments at once
        quotes = kite.quote(symbols)

        ce_oi, pe_oi = {}, {}
        for _, row in ce_rows.iterrows():
            key = f"NFO:{row['tradingsymbol']}"
            q   = quotes.get(key, {})
            oi  = int(q.get("oi", 0))
            if oi > 0:
                ce_oi[int(row["strike"])] = oi

        for _, row in pe_rows.iterrows():
            key = f"NFO:{row['tradingsymbol']}"
            q   = quotes.get(key, {})
            oi  = int(q.get("oi", 0))
            if oi > 0:
                pe_oi[int(row["strike"])] = oi

        if not ce_oi or not pe_oi:
            log.warning("OI: no OI data returned from Kite quotes")
            return None

        resistance = max(ce_oi, key=ce_oi.get)
        support    = max(pe_oi, key=pe_oi.get)
        total_ce   = sum(ce_oi.values())
        total_pe   = sum(pe_oi.values())
        pcr        = round(total_pe / total_ce, 2) if total_ce else 1.0

        # Max pain: strike where total option value is minimized
        all_s  = sorted(set(list(ce_oi) + list(pe_oi)))
        pain   = {}
        for s in all_s:
            pain[s] = (
                sum(max(0, s - k) * v for k, v in ce_oi.items()) +
                sum(max(0, k - s) * v for k, v in pe_oi.items())
            )
        max_pain = min(pain, key=pain.get)

        result = {
            "support"   : support,
            "resistance": resistance,
            "max_pain"  : max_pain,
            "pcr"       : pcr,
            "expiry"    : str(nearest),
            "bias"      : "BULLISH" if pcr > 1 else "BEARISH",
        }
        log.info(
            f"OI | Support={support} Resistance={resistance} "
            f"MaxPain={max_pain} PCR={pcr} Bias={result['bias']}"
        )
        return result

    except Exception as e:
        log.warning(f"OI fetch failed: {e}")
        return None


def is_trade_aligned_with_oi(direction: str, entry_price: float,
                              oi_levels: dict | None) -> bool:
    """
    Only blocks trades when price is dangerously close to a max-OI wall.
    PCR bias is NOT used — it's too blunt and blocks valid EMA signals.
    """
    if not oi_levels:
        return True  # don't block if OI unavailable

    resistance = oi_levels["resistance"]
    support    = oi_levels["support"]

    if direction == "BUY":
        # Block BUY only if price is approaching resistance from below
        if resistance > entry_price and entry_price >= (resistance - config.OI_BUFFER):
            log.info(f"OI blocked BUY — price {entry_price} near resistance {resistance}")
            return False
    else:
        # Block SELL only if price is near support but hasn't broken it yet
        # If price is already well below support, support is broken — don't block
        if support > entry_price + config.OI_BUFFER:
            pass  # price already broke below support, trade is fine
        elif entry_price <= (support + config.OI_BUFFER) and entry_price >= (support - config.OI_BUFFER):
            log.info(f"OI blocked SELL — price {entry_price} at support wall {support}")
            return False

    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    levels = get_oi_levels("NIFTY")
    if levels:
        print("\nNIFTY OI Levels:")
        for k, v in levels.items():
            print(f"  {k:14}: {v}")
    else:
        print("OI data unavailable")
