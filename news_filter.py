"""
News & Event Filter
Checks NSE + RBI for high-impact events.
Automatically skips or pauses trading on dangerous days.
Free — no API key needed.
"""
import logging
import requests
from datetime import date, datetime

import config

log = logging.getLogger(__name__)

_HIGH_IMPACT_KEYWORDS = [
    "rbi", "reserve bank", "repo rate", "monetary policy", "mpc",
    "federal reserve", "fed rate", "fomc", "powell",
    "inflation", "cpi", "gdp", "budget", "fiscal",
    "election", "exit poll", "sebi", "circuit breaker",
    "crude oil", "opec", "nonfarm", "unemployment",
]

_MARKET_HOLIDAYS = {
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31",
    "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01",
    "2025-08-15", "2025-08-27", "2025-10-02", "2025-10-20",
    "2025-10-21", "2025-10-23", "2025-11-05", "2025-11-15",
    "2025-12-25",
    # 2026 NSE holidays (confirmed + estimated for remaining year)
    "2026-01-26",  # Republic Day
    "2026-03-19",  # Holi
    "2026-04-02",  # Ram Navami
    "2026-04-03",  # Good Friday
    "2026-04-14",  # Dr. Ambedkar Jayanti / Baisakhi
    "2026-04-17",  # Easter Monday (tentative)
    "2026-05-01",  # Maharashtra Day / Labour Day
    "2026-07-17",  # Muharram (estimated)
    "2026-08-15",  # Independence Day
    "2026-08-25",  # Ganesh Chaturthi (estimated)
    "2026-10-02",  # Gandhi Jayanti
    "2026-10-20",  # Dussehra (estimated)
    "2026-11-04",  # Diwali Laxmi Puja (estimated)
    "2026-11-05",  # Diwali Balipratipada (estimated)
    "2026-11-25",  # Gurunanak Jayanti (estimated)
    "2026-12-25",  # Christmas
}

_RBI_MPC_DATES = {
    "2026-02-07", "2026-04-09", "2026-06-06",
    "2026-08-08", "2026-10-08", "2026-12-06",
}

_NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer"   : "https://www.nseindia.com",
}


def is_market_holiday(check_date: date | None = None) -> bool:
    return str(check_date or date.today()) in _MARKET_HOLIDAYS


def is_rbi_day(check_date: date | None = None) -> bool:
    return str(check_date or date.today()) in _RBI_MPC_DATES


def _fetch_nse_events() -> list[str]:
    events = []
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=_NSE_HEADERS, timeout=10)
        resp = session.get("https://www.nseindia.com/api/event-calendar",
                           headers=_NSE_HEADERS, timeout=10)
        if resp.status_code == 200:
            today_str = date.today().strftime("%d-%b-%Y").upper()
            for item in resp.json():
                if today_str in str(item.get("date", "")).upper():
                    events.append(str(item.get("purpose", "")).lower())
    except (requests.RequestException, ValueError) as e:
        log.warning(f"NSE event fetch failed: {e}")
    return events


def _fetch_rbi_headlines() -> list[str]:
    headlines = []
    try:
        resp      = requests.get("https://www.rbi.org.in/scripts/rss.aspx",
                                 headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        today_str = date.today().strftime("%d %b %Y").lower()
        for line in resp.text.lower().splitlines():
            if today_str in line:
                if any(kw in line for kw in ["repo", "rate", "policy", "mpc", "inflation"]):
                    headlines.append(line.strip())
    except requests.RequestException as e:
        log.warning(f"RBI RSS fetch failed: {e}")
    return headlines


def is_high_impact_news_day() -> tuple[bool, str]:
    today = date.today()

    if today.weekday() >= 5:
        return True, "Weekend — market closed"
    if is_market_holiday(today):
        return True, f"NSE market holiday: {today}"
    if is_rbi_day(today):
        return True, "RBI MPC announcement day — skipping"

    for event in _fetch_nse_events():
        if any(kw in event for kw in _HIGH_IMPACT_KEYWORDS):
            reason = f"High impact NSE event: {event[:60]}"
            log.warning(f"NEWS FILTER: {reason}")
            return True, reason

    headlines = _fetch_rbi_headlines()
    if headlines:
        reason = f"RBI news today: {headlines[0][:80]}"
        log.warning(f"NEWS FILTER: {reason}")
        return True, reason

    return False, "No high impact events — safe to trade"


def is_expiry_week() -> bool:
    """True if this week's Thursday is a NIFTY expiry (every Thursday)."""
    today = date.today()
    # Find this week's Thursday
    days_to_thursday = (3 - today.weekday()) % 7
    return days_to_thursday <= 3  # Mon-Thu of expiry week


def should_pause_trading(current_time_str: str | None = None) -> tuple[bool, str]:
    now_str = current_time_str or datetime.now().strftime("%H:%M")

    # Skip first 30 min of market — always volatile
    if config.MARKET_OPEN <= now_str < config.OPEN_VOLATILITY_END:
        return True, f"Opening volatility window ({config.MARKET_OPEN}–{config.OPEN_VOLATILITY_END})"

    # Pause 15 min before and 30 min after RBI announcement (~10:00 AM)
    if is_rbi_day():
        c_h, c_m   = map(int, now_str.split(":"))
        current_m  = c_h * 60 + c_m
        rbi_m      = 10 * 60
        if (rbi_m - 15) <= current_m <= (rbi_m + 30):
            return True, "Near RBI announcement window"

    return False, "Clear"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dangerous, reason = is_high_impact_news_day()
    print(f"\nSafe to trade : {not dangerous}")
    print(f"Reason        : {reason}")
    paused, p_reason = should_pause_trading()
    print(f"Paused now    : {paused}")
    print(f"Reason        : {p_reason}")
