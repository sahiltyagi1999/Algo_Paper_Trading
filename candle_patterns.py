"""
Shared candle pattern detection.
Used by both algo_trader.py and strategy_830.py.
"""
import config


def is_dominance(row) -> bool:
    """Body >= DOMINANCE_BODY % of total range."""
    total = row["high"] - row["low"]
    if total == 0:
        return False
    return (abs(row["close"] - row["open"]) / total) >= config.DOMINANCE_BODY


def is_rejection(row) -> bool:
    """Lower or upper wick >= REJECTION_WICK % of total range."""
    total = row["high"] - row["low"]
    if total == 0:
        return False
    body_top    = max(row["close"], row["open"])
    body_bottom = min(row["close"], row["open"])
    lower_wick  = body_bottom - row["low"]
    upper_wick  = row["high"] - body_top
    return (lower_wick / total) >= config.REJECTION_WICK or \
           (upper_wick / total) >= config.REJECTION_WICK


def is_bullish(row) -> bool:
    return row["close"] > row["open"]


def is_bearish(row) -> bool:
    return row["close"] < row["open"]
