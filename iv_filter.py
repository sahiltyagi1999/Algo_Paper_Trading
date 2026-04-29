"""
IV / VIX Filter
Fetches India VIX from NSE. High VIX = expensive options + volatile market.
Reduces position size automatically when VIX is elevated.
Free — no API key needed.
"""
import logging
import requests

log = logging.getLogger(__name__)

_VIX_LEVELS = {
    "VERY_LOW" : (0,  12,  1.00, True),
    "NORMAL"   : (12, 20,  1.00, True),
    "ELEVATED" : (20, 25,  0.50, True),
    "HIGH"     : (25, 30,  0.00, False),
    "DANGEROUS": (30, 999, 0.00, False),
}

_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}


def fetch_india_vix() -> float | None:
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=_HEADERS, timeout=10)
        resp    = session.get("https://www.nseindia.com/api/allIndices",
                              headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        for idx in resp.json().get("data", []):
            if idx.get("index") == "INDIA VIX":
                vix = float(idx["last"])
                log.info(f"India VIX: {vix}")
                return vix
        log.warning("India VIX not found in NSE response")
        return None
    except (requests.RequestException, KeyError, ValueError) as e:
        log.warning(f"VIX fetch failed: {e}")
        return None


def get_vix_status(vix: float | None = None) -> dict:
    if vix is None:
        vix = fetch_india_vix()

    if vix is None:
        return {"vix": None, "status": "UNKNOWN", "safe": True,
                "qty_multiplier": 1.0,
                "message": "VIX unavailable — proceeding with caution"}

    for status, (low, high, multiplier, safe) in _VIX_LEVELS.items():
        if low <= vix < high:
            messages = {
                "VERY_LOW" : f"VIX={vix:.2f} — calm market, good to trade",
                "NORMAL"   : f"VIX={vix:.2f} — normal conditions, safe to trade",
                "ELEVATED" : f"VIX={vix:.2f} — elevated, reducing position to 50%",
                "HIGH"     : f"VIX={vix:.2f} — high volatility, skipping trades",
                "DANGEROUS": f"VIX={vix:.2f} — market panic, DO NOT TRADE today",
            }
            result = {"vix": vix, "status": status, "safe": safe,
                      "qty_multiplier": multiplier, "message": messages[status]}
            log.info(result["message"])
            return result

    return {"vix": vix, "status": "UNKNOWN", "safe": True,
            "qty_multiplier": 1.0, "message": f"VIX={vix:.2f}"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = get_vix_status()
    print("\nIndia VIX Status:")
    for k, v in s.items():
        print(f"  {k:16}: {v}")
