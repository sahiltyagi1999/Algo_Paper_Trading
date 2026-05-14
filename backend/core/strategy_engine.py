import json, re, textwrap
import pandas as pd
import config

_CODE_SYSTEM = textwrap.dedent("""
    You are an expert algo trading engineer for the Indian options market (NSE).
    The user will describe a trading strategy in plain English.
    Write a single Python function named `detect_signal` that implements it.

    Signature: def detect_signal(df: "pd.DataFrame") -> dict | None:

    DataFrame columns (5-min candles, NIFTY/BANKNIFTY spot):
        open, high, low, close, volume, ema_fast, ema_slow, adx

    Return when signal:
        {"direction": "BUY"|"SELL", "entry_type": str, "entry": float,
         "sl": float, "target": float, "rr": int}
    Return None when no signal.

    Rules:
    - Only use stdlib + pandas + numpy. No other imports.
    - No side effects (no print, no I/O, no network).
    - Output ONLY the Python function — no markdown, no explanation.
""").strip()


def explain_signal_ema(df: pd.DataFrame) -> tuple[dict | None, dict]:
    """Return (signal, diagnostics) for the built-in 8-30 EMA strategy."""
    diag = {
        "strategy": "8-30 EMA",
        "reason": "",
        "signal": False,
    }
    if len(df) < config.EMA_SLOW + 5:
        diag["reason"] = f"need {config.EMA_SLOW + 5} candles, got {len(df)}"
        return None, diag
    last = df.iloc[-1]
    candle_time = str(last.name)
    diag.update({
        "candle_time": candle_time,
        "open": round(float(last["open"]), 2),
        "high": round(float(last["high"]), 2),
        "low": round(float(last["low"]), 2),
        "close": round(float(last["close"]), 2),
        "ema_fast": round(float(last["ema_fast"]), 2),
        "ema_slow": round(float(last["ema_slow"]), 2),
        "adx": round(float(last.get("adx", 0)), 2),
    })
    direction = "BUY" if last["ema_fast"] > last["ema_slow"] else "SELL"
    price     = last["close"]
    body      = abs(last["close"] - last["open"])
    rng       = last["high"] - last["low"]
    diag["direction"] = direction
    if rng == 0:
        diag["reason"] = "zero-range candle"
        return None, diag

    bullish      = last["close"] > last["open"]
    is_dominance = (body / rng) >= config.DOMINANCE_BODY
    is_rejection = (max(last["high"] - max(last["open"], last["close"]),
                        min(last["open"], last["close"]) - last["low"]) / rng) >= config.REJECTION_WICK
    proximity = abs(price - last["ema_slow"]) / price
    stretch = abs(last["ema_fast"] - last["ema_slow"]) / price
    diag.update({
        "bullish_candle": bool(bullish),
        "body_pct": round(float(body / rng * 100), 1),
        "dominance": bool(is_dominance),
        "rejection": bool(is_rejection),
        "ema_slow_proximity_pct": round(float(proximity * 100), 3),
        "ema_stretch_pct": round(float(stretch * 100), 3),
    })

    def _signal(entry_type, rr):
        prev = df.iloc[-2]
        # SL = previous candle's high (SELL) or low (BUY) — wider and more meaningful than signal candle
        sl    = prev["low"]  - config.SL_BUFFER if direction == "BUY" else prev["high"] + config.SL_BUFFER
        entry = last["high"] + config.ENTRY_BUFFER if direction == "BUY" else last["low"] - config.ENTRY_BUFFER
        risk  = abs(entry - sl)
        target = entry + risk * rr if direction == "BUY" else entry - risk * rr
        return {"direction": direction, "entry_type": entry_type,
                "entry": round(entry, 2), "sl": round(sl, 2), "target": round(target, 2),
                "candle": last.to_dict(), "candle_time": candle_time, "rr": rr}

    # Retest: price near EMA30 — trend must exist (EMAs must be separated), candle must match direction
    if proximity <= config.EMA30_PROXIMITY and (is_dominance or is_rejection) and stretch >= config.STRETCH_PCT:
        candle_matches = (direction == "BUY" and bullish) or (direction == "SELL" and not bullish)
        if candle_matches:
            sig = _signal("Retest", 3)
            diag.update({"reason": "Retest signal", "signal": True, "entry_type": "Retest"})
            return sig, diag
        diag["reason"] = f"Retest found but candle direction mismatch | dir={direction} bullish={bullish}"
        return None, diag

    # Continuation: EMAs stretched — dominance candle + direction must match trend
    # Price must be within 1% of EMA8 — not flying too far in either direction
    ema_fast_val = float(last["ema_fast"])
    prox_fast = abs(price - ema_fast_val) / price
    price_vs_ema8_ok = prox_fast <= 0.01
    candle_matches_trend = (direction == "BUY" and bullish) or (direction == "SELL" and not bullish)
    if stretch >= config.STRETCH_PCT and is_dominance and candle_matches_trend and price_vs_ema8_ok:
        sig = _signal("Continuation", 2)
        diag.update({"reason": "Continuation signal", "signal": True, "entry_type": "Continuation"})
        return sig, diag

    diag["reason"] = (
        f"filters failed: proximity {proximity*100:.2f}% "
        f"(limit {config.EMA30_PROXIMITY*100:.2f}%), stretch {stretch*100:.2f}% "
        f"(min {config.STRETCH_PCT*100:.2f}%), dominance={is_dominance}, "
        f"rejection={is_rejection}, candle_matches_trend={candle_matches_trend}"
    )
    return None, diag


def detect_signal_ema(df: pd.DataFrame) -> dict | None:
    return explain_signal_ema(df)[0]


def generate_strategy_code(strategy_prompt: str, openai_api_key: str) -> str:
    from openai import OpenAI
    resp = OpenAI(api_key=openai_api_key).chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": _CODE_SYSTEM}, {"role": "user", "content": strategy_prompt}],
        temperature=0, max_tokens=600,
    )
    code = resp.choices[0].message.content.strip()
    code = re.sub(r"^```(?:python)?\n?", "", code)
    code = re.sub(r"\n?```$", "", code)
    return code.strip()


def _make_code_runner(python_code: str):
    ns: dict = {}
    exec(compile(python_code, "<strategy>", "exec"), ns)  # noqa: S102
    fn = ns.get("detect_signal")
    if not callable(fn):
        raise ValueError("Generated code does not define detect_signal(df)")
    return fn


def run_ai_strategy_prompt(df: pd.DataFrame, prompt: str, openai_api_key: str) -> dict | None:
    try:
        from openai import OpenAI
        recent = df.tail(20)[["open", "high", "low", "close", "volume", "ema_fast", "ema_slow", "adx"]].round(2)
        resp = OpenAI(api_key=openai_api_key).chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "You are an expert algo trading signal engine for NSE India. "
                    'Return ONLY valid JSON: {"signal":"BUY"|"SELL"|"NONE","entry":<n>,"sl":<n>,"target":<n>,"reason":"<str>"}'
                )},
                {"role": "user", "content": f"Strategy:\n{prompt}\n\nCandles:\n{recent.to_json(orient='records')}"},
            ],
            temperature=0, max_tokens=200,
        )
        raw   = resp.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        result = json.loads(match.group())
        if result.get("signal") in ("BUY", "SELL"):
            return {"direction": result["signal"], "entry_type": "AI Strategy",
                    "entry": float(result.get("entry", df.iloc[-1]["close"])),
                    "sl": float(result.get("sl", 0)), "target": float(result.get("target", 0)),
                    "reason": result.get("reason", ""), "rr": 2}
    except Exception as e:
        print(f"[AI Strategy] {e}")
    return None


def get_strategy_runner(strategy_name: str | None, openai_api_key: str = "", find_strategy=None):
    if not strategy_name or strategy_name == "8-30 EMA":
        return lambda df: detect_signal_ema(df)

    strategy = (find_strategy or (lambda _: None))(strategy_name)
    if not strategy:
        return lambda df: detect_signal_ema(df)

    python_code = strategy.get("python_code", "").strip()
    if python_code:
        try:
            fn = _make_code_runner(python_code)
            return lambda df: fn(df)
        except Exception as e:
            print(f"[Strategy] Code exec failed: {e}")

    prompt = strategy.get("prompt", "").strip()
    if prompt and openai_api_key:
        return lambda df: run_ai_strategy_prompt(df, prompt, openai_api_key)

    return lambda df: detect_signal_ema(df)
