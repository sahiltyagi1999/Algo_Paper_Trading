"""
8-30 EMA Strategy (Paper Trading Simulator)
Strategy by: Wizard Trader (as described in video)

Rules:
- EMA 8 (fast) and EMA 30 (slow)
- Direction: EMA8 > EMA30 => BUY only | EMA30 > EMA8 => SELL only
- Entry 1 (Retest): Price pulls back to EMA30, dominance/rejection candle => 1:3 RR
- Entry 2 (Continuation): EMAs stretched apart, dominance candle breakout => 1:2 RR
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta


# ─── Candle Pattern Detection ────────────────────────────────────────────────

def is_dominance_candle(row, threshold=0.7):
    """Full-body candle: body >= 70% of total range."""
    total_range = row["High"] - row["Low"]
    if total_range == 0:
        return False
    body = abs(row["Close"] - row["Open"])
    return (body / total_range) >= threshold


def is_rejection_candle(row, threshold=0.6):
    """
    Hammer/shooting star: wick >= 60% of total range.
    Bullish rejection: long lower wick. Bearish: long upper wick.
    """
    total_range = row["High"] - row["Low"]
    if total_range == 0:
        return False
    body = abs(row["Close"] - row["Open"])
    upper_wick = row["High"] - max(row["Close"], row["Open"])
    lower_wick = min(row["Close"], row["Open"]) - row["Low"]
    return (lower_wick / total_range >= threshold) or (upper_wick / total_range >= threshold)


def is_bullish_candle(row):
    return row["Close"] > row["Open"]


def is_bearish_candle(row):
    return row["Close"] < row["Open"]


# ─── EMA Stretch Detection ────────────────────────────────────────────────────

def emas_are_stretched(row, stretch_pct=0.002):
    """
    True when EMA8 and EMA30 are far apart (gap > 0.2% of price).
    Used to detect continuation entry zones.
    """
    gap = abs(row["EMA8"] - row["EMA30"])
    return (gap / row["Close"]) >= stretch_pct


# ─── Signal Generation ───────────────────────────────────────────────────────

def generate_signals(df):
    df = df.copy()
    df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()
    df["EMA30"] = df["Close"].ewm(span=30, adjust=False).mean()

    df["Direction"] = np.where(df["EMA8"] > df["EMA30"], "BUY", "SELL")
    df["Crossover"] = df["Direction"] != df["Direction"].shift(1)
    df["Stretched"] = df.apply(emas_are_stretched, axis=1)

    df["IsDominance"] = df.apply(is_dominance_candle, axis=1)
    df["IsRejection"] = df.apply(is_rejection_candle, axis=1)

    signals = []

    for i in range(35, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        direction = row["Direction"]

        # ── Entry Type 1: Retest Entry ──────────────────────────────────────
        # Price comes back to EMA30 zone and shows dominance/rejection candle
        near_ema30 = abs(row["Low"] - row["EMA30"]) / row["EMA30"] <= 0.003
        candle_signal = (
            (row["IsDominance"] or row["IsRejection"]) and
            not row["Crossover"]  # not at the crossover point itself
        )

        if near_ema30 and candle_signal:
            if direction == "BUY" and is_bullish_candle(row):
                signals.append({
                    "Date": row.name,
                    "Type": "Retest",
                    "Direction": "BUY",
                    "Entry": row["High"],
                    "SL": row["Low"],
                    "RR": 3,
                })
            elif direction == "SELL" and is_bearish_candle(row):
                signals.append({
                    "Date": row.name,
                    "Type": "Retest",
                    "Direction": "SELL",
                    "Entry": row["Low"],
                    "SL": row["High"],
                    "RR": 3,
                })

        # ── Entry Type 2: Continuation Entry ───────────────────────────────
        # EMAs stretched, dominance candle breakout
        elif row["Stretched"] and row["IsDominance"]:
            if direction == "BUY" and is_bullish_candle(row):
                signals.append({
                    "Date": row.name,
                    "Type": "Continuation",
                    "Direction": "BUY",
                    "Entry": row["High"],  # enter on high breakout
                    "SL": row["Low"],
                    "RR": 2,
                })
            elif direction == "SELL" and is_bearish_candle(row):
                signals.append({
                    "Date": row.name,
                    "Type": "Continuation",
                    "Direction": "SELL",
                    "Entry": row["Low"],
                    "SL": row["High"],
                    "RR": 2,
                })

    return df, pd.DataFrame(signals)


# ─── Paper Trade Simulation ───────────────────────────────────────────────────

def simulate_trades(df, signals_df, capital=100000, risk_pct=0.01):
    """
    Simulate trades on historical data.
    risk_pct: risk 1% of capital per trade.
    """
    trades = []
    equity = capital
    equity_curve = [capital]

    for _, sig in signals_df.iterrows():
        entry = sig["Entry"]
        sl = sig["SL"]
        rr = sig["RR"]
        direction = sig["Direction"]

        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            continue

        risk_amount = equity * risk_pct
        qty = int(risk_amount / risk_per_unit)
        if qty == 0:
            continue

        target = (
            entry + risk_per_unit * rr if direction == "BUY"
            else entry - risk_per_unit * rr
        )

        # Check what happened after entry using future candles
        sig_date = sig["Date"]
        future = df[df.index > sig_date].head(20)  # look ahead 20 candles
        result = "OPEN"
        pnl = 0

        for _, frow in future.iterrows():
            if direction == "BUY":
                if frow["Low"] <= sl:
                    pnl = -risk_amount
                    result = "SL HIT"
                    break
                if frow["High"] >= target:
                    pnl = risk_amount * rr
                    result = "TARGET HIT"
                    break
            else:  # SELL
                if frow["High"] >= sl:
                    pnl = -risk_amount
                    result = "SL HIT"
                    break
                if frow["Low"] <= target:
                    pnl = risk_amount * rr
                    result = "TARGET HIT"
                    break

        if result == "OPEN":
            pnl = 0  # trade still open, ignore

        equity += pnl
        equity_curve.append(equity)

        trades.append({
            "Date": sig_date,
            "Type": sig["Type"],
            "Direction": direction,
            "Entry": round(entry, 2),
            "SL": round(sl, 2),
            "Target": round(target, 2),
            "RR": rr,
            "Qty": qty,
            "PnL": round(pnl, 2),
            "Result": result,
            "Equity": round(equity, 2),
        })

    return pd.DataFrame(trades), equity_curve


# ─── Performance Report ───────────────────────────────────────────────────────

def print_report(trades_df, equity_curve, capital):
    if trades_df.empty:
        print("No trades generated.")
        return

    closed = trades_df[trades_df["Result"] != "OPEN"]
    wins = closed[closed["Result"] == "TARGET HIT"]
    losses = closed[closed["Result"] == "SL HIT"]

    total = len(closed)
    win_rate = len(wins) / total * 100 if total else 0
    total_pnl = closed["PnL"].sum()
    final_equity = equity_curve[-1]

    print("\n" + "=" * 50)
    print("       8-30 EMA STRATEGY — BACKTEST REPORT")
    print("=" * 50)
    print(f"  Starting Capital   : ₹{capital:,.0f}")
    print(f"  Final Equity       : ₹{final_equity:,.0f}")
    print(f"  Net PnL            : ₹{total_pnl:,.0f}")
    print(f"  Return             : {(final_equity - capital) / capital * 100:.2f}%")
    print(f"  Total Trades       : {total}")
    print(f"  Wins               : {len(wins)}")
    print(f"  Losses             : {len(losses)}")
    print(f"  Win Rate           : {win_rate:.1f}%")
    print(f"  Avg Win            : ₹{wins['PnL'].mean():,.0f}" if len(wins) else "  Avg Win: N/A")
    print(f"  Avg Loss           : ₹{losses['PnL'].mean():,.0f}" if len(losses) else "  Avg Loss: N/A")

    max_dd = 0
    peak = equity_curve[0]
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100
        if dd > max_dd:
            max_dd = dd
    print(f"  Max Drawdown       : {max_dd:.2f}%")

    retest = closed[closed["Type"] == "Retest"]
    cont = closed[closed["Type"] == "Continuation"]
    if len(retest):
        rt_wr = len(retest[retest["Result"] == "TARGET HIT"]) / len(retest) * 100
        print(f"\n  Retest Entries     : {len(retest)} | Win Rate: {rt_wr:.1f}%")
    if len(cont):
        ct_wr = len(cont[cont["Result"] == "TARGET HIT"]) / len(cont) * 100
        print(f"  Continuation Entries: {len(cont)} | Win Rate: {ct_wr:.1f}%")

    print("=" * 50)
    print("\nRecent Trades:")
    print(trades_df[["Date", "Type", "Direction", "Entry", "SL", "Target", "RR", "PnL", "Result"]].tail(10).to_string(index=False))


# ─── Chart ────────────────────────────────────────────────────────────────────

def plot_chart(df, trades_df, ticker):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 9), gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle(f"8-30 EMA Strategy — {ticker}", fontsize=14, fontweight="bold")

    ax1.plot(df.index, df["Close"], color="#aaaaaa", linewidth=0.8, label="Price")
    ax1.plot(df.index, df["EMA8"], color="green", linewidth=1.2, label="EMA 8")
    ax1.plot(df.index, df["EMA30"], color="red", linewidth=1.2, label="EMA 30")

    for _, t in trades_df.iterrows():
        color = "lime" if t["Result"] == "TARGET HIT" else ("red" if t["Result"] == "SL HIT" else "gray")
        marker = "^" if t["Direction"] == "BUY" else "v"
        ax1.scatter(t["Date"], t["Entry"], color=color, marker=marker, s=80, zorder=5)

    ax1.set_ylabel("Price")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    equity = trades_df["Equity"].values if not trades_df.empty else []
    if len(equity):
        ax2.plot(range(len(equity)), equity, color="dodgerblue", linewidth=1.5)
        ax2.axhline(equity[0], color="gray", linestyle="--", linewidth=0.8)
        ax2.fill_between(range(len(equity)), equity[0], equity, alpha=0.2,
                         where=[e >= equity[0] for e in equity], color="green")
        ax2.fill_between(range(len(equity)), equity[0], equity, alpha=0.2,
                         where=[e < equity[0] for e in equity], color="red")

    ax2.set_ylabel("Equity (₹)")
    ax2.set_xlabel("Trade #")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/Users/sahil.tyagi/Desktop/file/strategy_830_chart.png", dpi=150)
    print("\nChart saved: strategy_830_chart.png")
    plt.show()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Configuration
    TICKER = "^NSEI"        # Nifty 50. Use "^NSEBANK" for BankNifty
    INTERVAL = "5m"         # 1m, 5m, 15m, 1h, 1d
    PERIOD = "60d"          # yfinance max for 5m is 60 days
    CAPITAL = 100_000       # starting capital in ₹
    RISK_PCT = 0.01         # risk 1% per trade

    print(f"Downloading {TICKER} ({INTERVAL}, {PERIOD})...")
    data = yf.download(TICKER, interval=INTERVAL, period=PERIOD, progress=False)

    if data.empty:
        print("No data downloaded. Check ticker/interval.")
        exit()

    # Flatten multi-level columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    print(f"Data loaded: {len(data)} candles ({data.index[0]} to {data.index[-1]})")

    df, signals_df = generate_signals(data)
    print(f"Signals generated: {len(signals_df)}")

    trades_df, equity_curve = simulate_trades(df, signals_df, CAPITAL, RISK_PCT)
    print_report(trades_df, equity_curve, CAPITAL)
    plot_chart(df, trades_df, TICKER)
