"""Generates the algo trading logic PDF in Hinglish."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

W, H = A4

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent], **kw)
    return s

S = {
    "cover_title": style("cover_title", "Title",
        fontSize=28, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=8, alignment=TA_CENTER, fontName="Helvetica-Bold"),

    "cover_sub": style("cover_sub",
        fontSize=14, textColor=colors.HexColor("#16213e"),
        spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica"),

    "cover_note": style("cover_note",
        fontSize=10, textColor=colors.HexColor("#555555"),
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Oblique"),

    "chapter": style("chapter",
        fontSize=18, textColor=colors.HexColor("#0f3460"),
        spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold",
        borderPad=4),

    "section": style("section",
        fontSize=13, textColor=colors.HexColor("#e94560"),
        spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold"),

    "subsection": style("subsection",
        fontSize=11, textColor=colors.HexColor("#0f3460"),
        spaceBefore=8, spaceAfter=3, fontName="Helvetica-Bold"),

    "body": style("body",
        fontSize=10, textColor=colors.HexColor("#222222"),
        spaceAfter=5, leading=16, alignment=TA_JUSTIFY,
        fontName="Helvetica"),

    "bullet": style("bullet",
        fontSize=10, textColor=colors.HexColor("#222222"),
        spaceAfter=3, leading=15, leftIndent=16,
        bulletIndent=4, fontName="Helvetica"),

    "code": style("code",
        fontSize=9, textColor=colors.HexColor("#1a1a2e"),
        backColor=colors.HexColor("#f0f4f8"),
        spaceAfter=4, leading=14, leftIndent=12,
        fontName="Courier", borderPad=6),

    "highlight": style("highlight",
        fontSize=10, textColor=colors.HexColor("#ffffff"),
        backColor=colors.HexColor("#0f3460"),
        spaceAfter=4, leading=15, leftIndent=8,
        fontName="Helvetica-Bold", borderPad=5),

    "appendix_term": style("appendix_term",
        fontSize=11, textColor=colors.HexColor("#e94560"),
        spaceAfter=1, fontName="Helvetica-Bold"),

    "appendix_def": style("appendix_def",
        fontSize=10, textColor=colors.HexColor("#333333"),
        spaceAfter=8, leading=15, leftIndent=12,
        fontName="Helvetica"),
}

def hr():
    return HRFlowable(width="100%", thickness=1,
                      color=colors.HexColor("#e94560"), spaceAfter=8)

def sp(h=6):
    return Spacer(1, h)

def P(text, s="body"):
    return Paragraph(text, S[s])

def flow_table(data, col_widths, header=True):
    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0 if header else -1),
         colors.HexColor("#0f3460")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 10),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f7f9fc"), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",(0, 0), (-1, -1), 7),
        ("RIGHTPADDING",(0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

# ── Document ──────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/Users/sahil.tyagi/Desktop/file/Algo_Trading_Guide.pdf",
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title="Algo Trading System — Complete Guide",
    author="Claude + Sahil",
)

story = []

# ═══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    sp(60),
    P("📈  Algo Trading System", "cover_title"),
    P("Complete Logic Guide — Hinglish Mein", "cover_sub"),
    sp(10),
    HRFlowable(width="60%", thickness=3, color=colors.HexColor("#e94560"),
               hAlign="CENTER", spaceAfter=10),
    sp(10),
    P("Instrument: NIFTY 50  •  Strategy: 8-30 EMA  •  Mode: Paper Trading", "cover_note"),
    P("Capital: ₹1,50,000  •  Risk per Trade: 1%  •  Max Trades/Day: 3", "cover_note"),
    sp(20),
    P("Yeh document tumhare liye banaya gaya hai taaki tum poora system samajh sako —", "cover_note"),
    P("kya ho raha hai, kyun ho raha hai, aur kaise ho raha hai.", "cover_note"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Table of Contents", "chapter"),
    hr(),
]

toc = [
    ["1.", "System Ka Overview — Bada Picture"],
    ["2.", "Pre-Market Checks — Trade Se Pehle Kya Hota Hai"],
    ["3.", "EMA Strategy — Core Logic"],
    ["4.", "Signal Detection — Trade Kab Leta Hai Algo"],
    ["5.", "Option Trading — Spot Se Option Mein Convert"],
    ["6.", "Position Sizing — Kitne Lots Khareedne Hain"],
    ["7.", "Paper Trade Engine — Execution Kaise Hoti Hai"],
    ["8.", "OI Filter — Support/Resistance Se Block"],
    ["9.", "Filters Summary — Sab Filters Ek Jagah"],
    ["10.", "Daily Flow — Subah Se Shaam Tak"],
    ["11.", "Config File — Tumhare Haath Mein Kya Hai"],
    ["Appendix", "Sabhi Words Ka Matlab"],
]
toc_table = flow_table(
    [["#", "Chapter"]] + toc,
    [1.5*cm, 13*cm],
)
story += [toc_table, PageBreak()]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 1: System Ka Overview", "chapter"),
    hr(),
    P("Yeh ek <b>automated paper trading system</b> hai jo NIFTY 50 index ke options mein trade karta hai. "
      "'Paper trading' matlab — real paisa nahi lagta, lekin sab kuch exactly waise hi hota hai jaise real trading mein hota. "
      "Iska purpose hai 1 mahine ka genuine data collect karna — winners, losers, win rate — taaki real money lagate waqt "
      "confident ho sako ki strategy kaam karti hai."),
    sp(4),
    P("System 4 main cheezein karta hai:", "section"),
    P("• <b>Monitor karta hai</b> — Nifty ka price har 5 minute mein", "bullet"),
    P("• <b>Signal dhundhta hai</b> — EMA 8 aur EMA 30 ke basis par", "bullet"),
    P("• <b>Filters lagate hai</b> — VIX, news, OI, candle patterns", "bullet"),
    P("• <b>Trade karta hai</b> — Option buy karta hai, SL/target track karta hai, EOD close karta hai", "bullet"),
    sp(8),
    P("Files Ka Structure", "section"),
    flow_table([
        ["File", "Kaam Kya Hai"],
        ["algo_trader.py", "Main brain — poora loop yahan chalata hai"],
        ["paper_trade.py", "Trade engine — order place/close/track karta hai"],
        ["option_chain.py", "Kite API se real option price fetch karta hai"],
        ["oi_data.py", "OI levels (support/resistance) fetch karta hai"],
        ["candle_patterns.py", "Candle kaisi hai — dominance ya rejection"],
        ["iv_filter.py", "India VIX check karta hai"],
        ["news_filter.py", "Aaj koi bada event toh nahi?"],
        ["config.py", "Sab settings yahan hain — tum yahan hi changes karo"],
        ["dashboard_server.py", "Web dashboard chalata hai (localhost:4200)"],
        ["report.py", "Trade alerts print karta hai, daily JSON save karta hai"],
    ], [4.5*cm, 10.5*cm]),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — PRE-MARKET CHECKS
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 2: Pre-Market Checks", "chapter"),
    hr(),
    P("Algo subah run karo toh 9:15 se pehle yeh 3 cheezein check karta hai. "
      "Agar koi bhi fail ho gayi, algo <b>poora din trade nahi karta</b>."),
    sp(6),

    P("Check 1 — News Filter", "section"),
    P("news_filter.py check karta hai:"),
    P("• Aaj market holiday toh nahi? (BSE/NSE calendar)"),
    P("• RBI MPC meeting aaj hai? (Interest rate decision wale din volatility bahut zyada hoti hai)"),
    P("• Koi NSE special event?"),
    P("Agar haan — algo band ho jaata hai. Reason: intraday mein unexpected moves aate hain jo EMA strategy ko fool karte hain.", "body"),
    sp(6),

    P("Check 2 — VIX Filter", "section"),
    P("India VIX = market ki 'fear gauge'. Jitna zyada VIX, utna zyada uncertainty."),
    flow_table([
        ["VIX Range", "Status", "Position Size", "Kya Matlab"],
        ["Below 12", "VERY LOW", "100%", "Market soya hua hai, trend nahi milega"],
        ["12–20", "NORMAL", "100%", "Sweet spot — EMA strategy best kaam karti hai"],
        ["20–25", "ELEVATED", "50%", "Thoda risk, half lots lo"],
        ["25–30", "HIGH", "0% — Skip", "Bahut volatile, mat khelo"],
        ["30+", "DANGEROUS", "0% — Skip", "Market mein aag lagi hai, bahar raho"],
    ], [3*cm, 3*cm, 3*cm, 5.5*cm]),
    sp(6),

    P("Check 3 — OI Levels (Pre-Market)", "section"),
    P("Option chain se support aur resistance levels nikalte hain. Yeh sirf information ke liye hain — "
      "actual blocking trading hours mein hoti hai (Chapter 8 mein detail)."),
    sp(6),

    P("Opening Volatility Window — 9:15 to 9:45", "section"),
    P("Market khulne ke pehle 30 minute mein algo koi bhi trade nahi leta. "
      "Reason: opening mein bahut sare fake moves aate hain — institutions apni positions set karte hain, "
      "retail traders panic karte hain. Yeh moves often reverse ho jaate hain. "
      "9:45 ke baad market settle ho jaata hai aur genuine trend shuru hota hai.", "body"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — EMA STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 3: EMA Strategy — Core Logic", "chapter"),
    hr(),

    P("EMA Kya Hota Hai?", "section"),
    P("EMA = Exponential Moving Average. Yeh price ka ek smoothed version hai jo recent prices ko "
      "zyada importance deta hai aur old prices ko kam. Simple Moving Average (SMA) se better hai "
      "kyunki yeh price changes par faster react karta hai.", "body"),
    sp(4),

    P("Humara Setup: EMA 8 aur EMA 30", "section"),
    P("• <b>EMA 8</b> = Last 8 candles ka average — fast line, price ke karib rehta hai", "bullet"),
    P("• <b>EMA 30</b> = Last 30 candles ka average — slow line, trend dikhata hai", "bullet"),
    sp(4),

    flow_table([
        ["Condition", "Direction", "Matlab"],
        ["EMA 8 > EMA 30", "BUY (Bullish)", "Short term average upar — uptrend hai"],
        ["EMA 8 < EMA 30", "SELL (Bearish)", "Short term average neeche — downtrend hai"],
    ], [5*cm, 4*cm, 5.5*cm]),
    sp(6),

    P("ADX — Trend Ki Strength Naapna", "section"),
    P("Sirf EMA cross kafi nahi. Market sideways bhi ho sakta hai jab EMA 8 aur EMA 30 "
      "ek doosre ke karib hote hain. Isliye ADX use karte hain.", "body"),
    sp(3),
    P("ADX = Average Directional Index. Yeh 0-100 ke beech hota hai:"),
    P("• ADX < 20 → Market sideways hai — algo trade nahi leta", "bullet"),
    P("• ADX 20-40 → Moderate trend — trade lete hain", "bullet"),
    P("• ADX 40+ → Strong trend — best conditions", "bullet"),
    sp(6),

    P("Candle Patterns — Quality Check", "section"),
    P("Har signal mein candle ka shape bhi check hota hai:"),
    sp(3),
    flow_table([
        ["Pattern", "Condition", "Matlab"],
        ["Dominance Candle", "Body ≥ 65% of candle range", "Strong buyers/sellers — conviction hai"],
        ["Rejection Candle", "Wick ≥ 55% of candle range", "Price ek level se wapas aaya — rejection hui"],
        ["Bullish", "Close > Open", "Green candle — buyers jeet gaye"],
        ["Bearish", "Close < Open", "Red candle — sellers jeet gaye"],
    ], [4*cm, 5*cm, 5.5*cm]),
    sp(4),
    P("Candle Range = High - Low (candle ki poori height)", "code"),
    P("Body = |Close - Open| (sirf real body ki height)", "code"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — SIGNAL DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 4: Signal Detection — Trade Kab Leta Hai", "chapter"),
    hr(),
    P("Do types ke entry signals hain. Dono mein ADX > 20 hona zaroori hai."),
    sp(6),

    P("Entry Type 1 — Retest Entry (1:3 Risk:Reward)", "section"),
    P("Yeh tab hota hai jab price EMA 30 ke paas wapas aata hai aur ek achhi candle banaata hai."),
    sp(3),
    P("Sochne ka tarika: EMA 30 ek 'road' ki tarah hai. Price usse door jaata hai, "
      "phir wapas aata hai (retest karta hai), aur phir phir se trend ki direction mein jaata hai. "
      "Yeh ek high-probability trade hai kyunki hum trend ke saath ja rahe hain.", "body"),
    sp(4),
    P("Conditions for BUY Retest:", "subsection"),
    P("• EMA 8 > EMA 30 (uptrend)", "bullet"),
    P("• Price EMA 30 ke 0.4% ke andar hai", "bullet"),
    P("• Candle dominance ya rejection hai", "bullet"),
    P("• Candle bullish hai (green)", "bullet"),
    P("• ADX > 20", "bullet"),
    sp(3),
    P("Conditions for SELL Retest:", "subsection"),
    P("• EMA 8 < EMA 30 (downtrend)", "bullet"),
    P("• Price EMA 30 ke 0.4% ke andar hai", "bullet"),
    P("• Candle dominance ya rejection hai", "bullet"),
    P("• Candle bearish hai (red)", "bullet"),
    P("• ADX > 20", "bullet"),
    sp(6),

    P("Entry Type 2 — Continuation Entry (1:2 Risk:Reward)", "section"),
    P("Yeh tab hota hai jab EMA 8 aur EMA 30 bahut door ho jaate hain — matlab trend bahut strong hai — "
      "aur ek strong candle banaata hai. Hum trend ke momentum mein jump karte hain.", "body"),
    sp(4),
    P("EMA Gap 'Stretched' kab hota hai?", "subsection"),
    P("Jab EMA 8 aur EMA 30 ke beech ka gap, current price ka 0.3% se zyada ho.", "body"),
    P("Formula: |EMA8 - EMA30| / Price ≥ 0.003", "code"),
    sp(4),
    P("Conditions for Continuation:", "subsection"),
    P("• EMAs stretched hain", "bullet"),
    P("• Dominance candle hai (strong body)", "bullet"),
    P("• Direction ke according bullish/bearish", "bullet"),
    P("• ADX > 20", "bullet"),
    sp(6),

    P("SL aur Target Kaise Calculate Hote Hain", "section"),
    flow_table([
        ["Parameter", "BUY ke liye", "SELL ke liye"],
        ["Entry", "Candle High + 0.5 pts buffer", "Candle Low - 0.5 pts buffer"],
        ["Stop Loss (SL)", "Candle Low - 2 pts buffer", "Candle High + 2 pts buffer"],
        ["Target (Retest)", "Entry + (Risk × 3)", "Entry - (Risk × 3)"],
        ["Target (Continuation)", "Entry + (Risk × 2)", "Entry - (Risk × 2)"],
    ], [4.5*cm, 4.5*cm, 5.5*cm]),
    sp(4),
    P("Risk = |Entry - SL| (ek trade mein kitna point risk le rahe hain)", "code"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — OPTION TRADING
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 5: Option Trading — Spot Se Option Mein Convert", "chapter"),
    hr(),
    P("Algo directly Nifty index mein trade nahi karta — woh <b>options khareedta hai</b>. "
      "Kyun? Kyunki options mein limited risk hoti hai (sirf premium lost ho sakta hai) aur "
      "leverage milta hai (thode paison mein bada position).", "body"),
    sp(6),

    P("Option Type Kaunsa Lete Hain?", "section"),
    flow_table([
        ["Signal Direction", "Option Type", "Kyun"],
        ["BUY (Bullish)", "CALL option (CE)", "Call ka price badhta hai jab Nifty upar jaata hai"],
        ["SELL (Bearish)", "PUT option (PE)", "Put ka price badhta hai jab Nifty neeche jaata hai"],
    ], [4.5*cm, 4*cm, 6*cm]),
    sp(6),

    P("ATM Strike Kya Hai?", "section"),
    P("ATM = At The Money. Jis strike price par option ka premium sabse realistic hota hai "
      "(na bahut deep in-the-money, na bahut out-of-the-money). "
      "Hum hamesha ATM option lete hain.", "body"),
    sp(3),
    P("NIFTY ATM Calculation:", "subsection"),
    P("Strike = Round(Spot / 50) × 50", "code"),
    P("Example: Nifty = 24,341 → ATM = Round(24341/50)×50 = 487×50 = 24,350 CE/PE", "code"),
    sp(6),

    P("Delta — Spot Se Option Price Ka Connection", "section"),
    P("Delta batata hai ki Nifty 1 point move karne par option premium kitna move karega."),
    sp(3),
    P("ATM option ka delta ≈ 0.5 (approximately)"),
    P("Matlab: Nifty 10 points upar gaya → Call option premium ≈ 5 rupaye badhega", "body"),
    sp(4),
    P("Spot SL/Target ko Option SL/Target mein convert karna:", "subsection"),
    P("Option SL     = Option Entry - (Spot Risk   × 0.5)", "code"),
    P("Option Target = Option Entry + (Spot Reward × 0.5)", "code"),
    sp(3),
    P("Example:", "subsection"),
    P("Nifty spot entry = 24,400  |  Spot SL = 24,390  |  Spot Target = 24,430"),
    P("Spot Risk = 10 pts  |  Spot Reward = 30 pts", "body"),
    P("Option Entry = ₹248  |  Option SL = 248 - (10×0.5) = ₹243  |  Option Target = 248 + (30×0.5) = ₹263", "code"),
    sp(6),

    P("Expiry — Kaunse Week Ka Option?", "section"),
    P("NIFTY ke weekly options har Thursday ko expire hote hain. "
      "Expiry ke din zero-value contracts se bachne ke liye algo automatically "
      "agle hafte ka option select karta hai.", "body"),
    sp(3),
    P("Lot Size — NIFTY ka 1 lot = 65 shares (Nov 2024 ke baad revised)", "highlight"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — POSITION SIZING
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 6: Position Sizing — Kitne Lots Khareedne Hain", "chapter"),
    hr(),
    P("Yeh sabse important chapter hai. Galat position sizing se poori capital khatam ho sakti hai. "
      "Humara system do rules se protect karta hai:", "body"),
    sp(6),

    P("Rule 1 — Risk-Based Sizing (1% per trade)", "section"),
    P("Ek trade mein maximum 1% capital risk ho sakti hai = ₹1,500 (on ₹1.5L capital)."),
    sp(3),
    P("Formula:", "subsection"),
    P("Risk Amount    = Capital × 1%  = ₹1,500", "code"),
    P("Risk Per Lot   = (Option Entry - Option SL) × Lot Size", "code"),
    P("Lots           = Risk Amount / Risk Per Lot", "code"),
    sp(3),
    P("Example:", "subsection"),
    P("Option Entry=248, Option SL=238, Lot Size=65"),
    P("Risk Per Lot = (248-238) × 65 = ₹650"),
    P("Lots = 1500 / 650 = 2 lots (rounded down)", "code"),
    sp(6),

    P("Rule 2 — Capital Cap (30% max per trade)", "section"),
    P("Kabhi kabhi spot SL bahut tight hoti hai (5-6 pts), jisse opt_risk_per_lot bahut kam hoti hai, "
      "aur lots count bahut zyada ho jaata hai. Isliye hard cap lagaya hai:", "body"),
    sp(3),
    P("Max Lots by Capital = (Capital × 30%) / Lot Value", "code"),
    P("Final Lots = min(Risk-based lots, Capital-cap lots)", "code"),
    sp(3),
    P("Example: ₹1.5L × 30% = ₹45,000 max  |  Lot Value = ₹16,120  →  Max 2 lots", "code"),
    sp(6),

    P("VIX Multiplier", "section"),
    P("Agar VIX elevated hai, lots automatically reduce hote hain:"),
    flow_table([
        ["VIX Level", "Multiplier", "Effect"],
        ["Below 20", "1.0 (100%)", "Normal sizing"],
        ["20–25", "0.5 (50%)", "Half lots"],
        ["Above 25", "0.0 (0%)", "Trade skip"],
    ], [4.5*cm, 4*cm, 6*cm]),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — PAPER TRADE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 7: Paper Trade Engine", "chapter"),
    hr(),
    P("paper_trade.py ek virtual broker ki tarah kaam karta hai. "
      "Koi real order Zerodha tak nahi jaata — sab simulation mein hota hai. "
      "Lekin prices 100% real hain — Kite API se live fetch hote hain.", "body"),
    sp(6),

    P("Trade Ka Lifecycle", "section"),
    flow_table([
        ["Step", "Kya Hota Hai", "Kahan Se Data"],
        ["1. Entry", "Trade create hota hai, premium store hoti hai", "Kite API — live LTP"],
        ["2. Monitoring", "Har candle par high/low check hota hai spot ke against", "Kite API — live candles"],
        ["3. SL Hit", "Spot candle low ≤ Spot SL → exit trigger", "Kite API — live option LTP at that moment"],
        ["4. Target Hit", "Spot candle high ≥ Spot Target → exit trigger", "Kite API — live option LTP at that moment"],
        ["5. EOD Close", "15:20 par sab open trades close", "Kite API — final live LTP"],
        ["6. CSV Save", "Trade record permanent CSV mein", "logs/daily_report.csv"],
    ], [1.5*cm, 6*cm, 6*cm]),
    sp(6),

    P("PnL Calculation", "section"),
    P("PnL = (Exit Price - Entry Price) × Qty", "code"),
    P("Total Cost = Entry Price × Qty", "code"),
    P("Exit Value = Exit Price × Qty", "code"),
    sp(3),
    P("Example: Entry=248, Exit=263, Qty=130 (2 lots × 65)"),
    P("PnL = (263-248) × 130 = 15 × 130 = +₹1,950", "code"),
    sp(6),

    P("Safety Guards", "section"),
    P("• MAX_TRADES_DAY = 3 → 3 se zyada trades nahi", "bullet"),
    P("• DAILY_LOSS_LIMIT = ₹4,500 → itna loss ho jaaye toh band", "bullet"),
    P("• Daily reset → naya din, naye counters (PnL, trade count, open trades clear)", "bullet"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — OI FILTER
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 8: OI Filter — Support/Resistance", "chapter"),
    hr(),
    P("OI = Open Interest. Yeh batata hai ki kitne contracts abhi bhi open hain. "
      "Jis strike par sabse zyada Put OI hai → woh support hai (log wahan puts khareed kar neeche jana nahi chahte). "
      "Jis strike par sabse zyada Call OI hai → woh resistance hai.", "body"),
    sp(6),

    P("OI Se Support/Resistance Kaise Milti Hai?", "section"),
    P("• Algo current spot ke aas paas ke ±10 strikes scan karta hai", "bullet"),
    P("• Har strike ka PE OI aur CE OI Kite se fetch karta hai", "bullet"),
    P("• Sabse zyada PE OI wali strike = Support", "bullet"),
    P("• Sabse zyada CE OI wali strike = Resistance", "bullet"),
    sp(6),

    P("Trade Block Kab Hota Hai?", "section"),
    flow_table([
        ["Signal", "Block Condition", "Logic"],
        ["BUY", "Price ≥ Resistance - 50 pts", "Resistance ke paas BUY risky hai — ceiling hai wahan"],
        ["SELL", "Price is right at Support wall (±50 pts)", "Support pe sell risky — floor tod bhi sakta hai"],
        ["SELL", "Price already below support by >50 pts", "Support toot chuka — freely trade karo"],
    ], [2.5*cm, 5.5*cm, 6.5*cm]),
    sp(6),

    P("OI Refresh — Har 30 Minute Mein", "section"),
    P("OI static nahi hota — institutions positions change karte hain during the day. "
      "Isliye har 30 minute mein fresh OI levels fetch karta hai. "
      "Agar Kite unavailable ho toh OI filter skip ho jaata hai — trade block nahi hota.", "body"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9 — FILTERS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 9: Sab Filters Ek Jagah", "chapter"),
    hr(),
    P("Ek trade tab tak nahi hota jab tak yeh saare gates clear na ho jaayein:"),
    sp(6),
    flow_table([
        ["Filter", "Source", "Block Condition", "Adjustment"],
        ["Holiday", "news_filter.py", "Aaj market band hai", "Poora din skip"],
        ["RBI/Event", "news_filter.py", "High-impact event aaj hai", "Poora din skip"],
        ["VIX", "iv_filter.py", "VIX ≥ 25", "Skip day  |  VIX 20-25 → half lots"],
        ["Opening Window", "news_filter.py", "Time < 9:45 AM", "Wait karo"],
        ["ADX", "algo_trader.py", "ADX < 20", "Sideways market — skip candle"],
        ["No Trade After", "algo_trader.py", "Time ≥ 15:00", "No new entries"],
        ["Candle Pattern", "candle_patterns.py", "Not dominance or rejection", "Skip signal"],
        ["OI Wall", "oi_data.py", "Price near max-OI level", "Skip signal"],
        ["Liquidity", "algo_trader.py", "Volume < 100 OR OI < 500", "Option illiquid — skip"],
        ["Max Trades", "paper_trade.py", "Trade count ≥ 3", "No more trades today"],
        ["Daily Loss", "paper_trade.py", "Day loss ≥ ₹4,500", "Stop trading today"],
    ], [3.5*cm, 3.5*cm, 4*cm, 3.5*cm]),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 10 — DAILY FLOW
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 10: Daily Flow — Subah Se Shaam Tak", "chapter"),
    hr(),
    flow_table([
        ["Time", "Kya Hota Hai"],
        ["Before 9:15", "python3 zerodha_login.py → fresh access token lo"],
        ["Before 9:15", "python3 algo_trader.py → algo shuru karo"],
        ["Before 9:15", "Pre-market checks: News → VIX → OI levels"],
        ["9:15", "Market open — algo loop shuru"],
        ["9:15–9:45", "Opening window — sirf monitor, koi trade nahi"],
        ["9:45 onwards", "Har 5 min: candle fetch → indicators → signal check → filters → trade?"],
        ["Every 30 min", "OI levels refresh (spot ke aas paas ke strikes)"],
        ["Every 5 min", "Open trades ka SL/Target check karo"],
        ["Anytime", "SL hit ya Target hit → live Kite LTP se exit, CSV mein save"],
        ["15:00", "Koi nayi entry nahi (NO_TRADE_AFTER)"],
        ["15:20", "Market close — sab open trades Kite live LTP pe close"],
        ["15:20", "Daily report print + JSON save in logs/"],
        ["15:20", "python3 dashboard_server.py → browser mein dekho"],
    ], [3.5*cm, 11*cm]),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 11 — CONFIG FILE
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Chapter 11: Config File — Tumhare Haath Mein Kya Hai", "chapter"),
    hr(),
    P("config.py ek file hai jise tum directly edit kar sakte ho bina rest of the code ko samjhe. "
      "Yahan sab important settings hain:", "body"),
    sp(6),
    flow_table([
        ["Setting", "Current Value", "Kya Karta Hai", "Suggestion"],
        ["CAPITAL", "₹1,50,000", "Starting capital", "Real money mein same rakhna"],
        ["RISK_PCT", "0.01 (1%)", "Risk per trade", "1% safe hai beginners ke liye"],
        ["MAX_TRADES_DAY", "3", "Max trades/day", "3 enough hai — quality over quantity"],
        ["DAILY_LOSS_LIMIT", "₹4,500", "Day stop-loss", "3 trades × ₹1,500 = ₹4,500"],
        ["TIMEFRAME", "5 minutes", "Candle size", "5 min best for intraday options"],
        ["EMA_FAST", "8", "Fast EMA period", "Standard — change nahi karna"],
        ["EMA_SLOW", "30", "Slow EMA period", "Standard — change nahi karna"],
        ["ADX_THRESHOLD", "20", "Min trend strength", "20 safe — 15 par zyada trades"],
        ["OI_BUFFER", "50 pts", "OI wall buffer zone", "50 best — 100 zyada block karta tha"],
        ["NO_TRADE_AFTER", "15:00", "Last entry time", "15:00 safe — expiry risk avoid"],
    ], [3.5*cm, 2.5*cm, 4*cm, 4.5*cm]),
    sp(6),
    P("Suggestion: Paper trading complete hone ke baad in settings ko backtest results ke "
      "basis par fine-tune karna. Ek mahine baad tumhare paas real data hoga — "
      "tab decide karna ki ADX threshold badhana hai ya kam karna, "
      "risk 1% rakhna hai ya 1.5% karna.", "body"),
    PageBreak(),
]

# ═══════════════════════════════════════════════════════════════════════════════
# APPENDIX — GLOSSARY
# ═══════════════════════════════════════════════════════════════════════════════
story += [
    P("Appendix: Sabhi Words Ka Matlab", "chapter"),
    hr(),
    P("Yahan har woh word explain kiya gaya hai jo document ya logs mein aata hai.", "body"),
    sp(8),
]

glossary = [
    ("ADX (Average Directional Index)",
     "Trend ki strength naapne wala indicator. 0-100 ke beech. 20 se upar ho toh trending market. "
     "Sideways market mein ADX neeche hota hai — tab algo trade nahi leta."),

    ("ATM (At The Money)",
     "Woh option strike jo current spot price ke sabse karib hoti hai. "
     "Example: Nifty 24,341 par hai toh ATM strike 24,350 hogi."),

    ("Bid / Ask",
     "Bid = sabse zyada price jo buyer dene ko ready hai. Ask = sabse kam price jo seller lene ko ready hai. "
     "Tum hamesha Ask par khareedoge aur Bid par bechoge."),

    ("Call Option (CE)",
     "Ek contract jo tumhe right deta hai Nifty ko ek fixed price par khareedne ka. "
     "Jab Nifty upar jaata hai, Call ka premium badhta hai."),

    ("Capital",
     "Trading ke liye available total paisa. Hamare case mein ₹1,50,000."),

    ("Continuation Entry",
     "Jab EMA 8 aur EMA 30 bahut door ho jaate hain (stretched) aur ek strong candle bane, "
     "tab trend ke saath trade karte hain. 1:2 risk:reward."),

    ("Delta",
     "Option ka sensitivity measure. ATM option ka delta ≈ 0.5 matlab Nifty 1 point move kare "
     "toh option premium 0.5 point move karega."),

    ("Dominance Candle",
     "Ek candle jiska body (open-close gap) overall range (high-low) ka 65% ya zyada ho. "
     "Strong directional move dikhata hai."),

    ("EMA (Exponential Moving Average)",
     "Price ka weighted average jisme recent prices ko zyada importance dete hain. "
     "EMA 8 = fast, EMA 30 = slow."),

    ("EOD (End of Day)",
     "Trading day ka end. 15:20 IST par algo sab open positions close kar deta hai."),

    ("Expiry",
     "Woh date jab option contract expire ho jaata hai. NIFTY weekly options har Thursday expire hote hain."),

    ("India VIX",
     "NSE ka volatility index. Market mein kitna fear hai uska measure. "
     "20 se neeche = normal, 25 se upar = dangerous."),

    ("Kite API",
     "Zerodha ka programming interface. Isse real-time prices, candles, option data fetch karte hain."),

    ("Liquidity",
     "Option mein kitna trading volume aur open interest hai. Kam liquidity wale options avoid karte hain "
     "kyunki bid-ask spread bahut wide hoti hai."),

    ("Lot",
     "Options ek fixed quantity mein aate hain. NIFTY ka 1 lot = 65 shares."),

    ("Lot Value",
     "Ek lot ki total cost. = LTP × Lot Size. Example: ₹248 × 65 = ₹16,120."),

    ("LTP (Last Traded Price)",
     "Woh price par sabse recent trade hua. Yahi hamare entry/exit price hote hain."),

    ("MPC (Monetary Policy Committee)",
     "RBI ki committee jo interest rates decide karti hai. Iske meetings wale din market volatile hoti hai."),

    ("OI (Open Interest)",
     "Abhi kitne option contracts open hain (na beca, na expire hua). "
     "High PE OI = support. High CE OI = resistance."),

    ("Paper Trading",
     "Simulated trading — real paisa nahi lagta lekin sab calculations real prices se hoti hain. "
     "Strategy test karne ka best tarika."),

    ("PCR (Put-Call Ratio)",
     "Total Put OI / Total Call OI. PCR > 1 = zyada puts = bullish sentiment (hedging). "
     "PCR < 1 = zyada calls = bearish sentiment."),

    ("Put Option (PE)",
     "Ek contract jo tumhe right deta hai Nifty ko ek fixed price par bechne ka. "
     "Jab Nifty neeche jaata hai, Put ka premium badhta hai."),

    ("Rejection Candle",
     "Ek candle jiska wick (shadow) overall range ka 55% ya zyada ho. "
     "Price ek level se reject hua — wapas aa gaya."),

    ("Resistance",
     "Woh price level jahan sellers strong hote hain aur price upar jaane se ruk jaati hai. "
     "Max CE OI wali strike."),

    ("Retest Entry",
     "Jab price EMA 30 ke paas wapas aata hai aur bounce karta hai. High probability setup. 1:3 risk:reward."),

    ("Risk:Reward (RR)",
     "Risk kitna hai vs Reward kitna mil sakta hai. 1:3 matlab ₹1 risk par ₹3 ka potential profit."),

    ("SL (Stop Loss)",
     "Woh price jahan par agar market jaaye, trade automatically close ho jaata hai "
     "aur aur loss book ho jaata hai."),

    ("Spot Price",
     "Nifty index ka actual current price. Options is price se derive hote hain."),

    ("Strike Price",
     "Woh fixed price jo option contract mein hota hai. Example: NIFTY 24400 CE mein 24400 = strike."),

    ("Support",
     "Woh price level jahan buyers strong hote hain aur price neeche jaane se ruk jaati hai. "
     "Max PE OI wali strike."),

    ("Target",
     "Woh price jahan par trade automatically close ho jaata hai aur profit book hota hai."),

    ("Trend",
     "Price ki consistent direction — ya toh upar (uptrend/bullish) ya neeche (downtrend/bearish)."),

    ("VIX",
     "Volatility Index. Dekho India VIX."),

    ("Weekly Expiry",
     "NIFTY options har hafte Thursday ko expire hote hain. BANKNIFTY bhi weekly."),
]

for term, definition in glossary:
    story.append(P(term, "appendix_term"))
    story.append(P(definition, "appendix_def"))

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD
# ═══════════════════════════════════════════════════════════════════════════════
doc.build(story)
print("PDF generated: Algo_Trading_Guide.pdf")
