function H2({ id, children }) {
  return <h2 id={id} style={{ fontSize: 16, fontWeight: 700, color: "#3fb950", margin: "28px 0 10px", paddingBottom: 6, borderBottom: "1px solid #21262d" }}>{children}</h2>;
}
function H3({ children }) {
  return <h3 style={{ fontSize: 14, fontWeight: 600, color: "#e6edf3", margin: "18px 0 8px" }}>{children}</h3>;
}
function P({ children }) {
  return <p style={{ fontSize: 13, color: "#8b949e", lineHeight: 1.8, marginBottom: 10 }}>{children}</p>;
}
function Code({ children }) {
  return <code style={{ fontFamily: '"SF Mono","Consolas",monospace', background: "#0d1117", border: "1px solid #30363d", borderRadius: 4, padding: "2px 6px", fontSize: 12, color: "#79c0ff" }}>{children}</code>;
}
function Pre({ children }) {
  return <pre style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 6, padding: "14px 16px", overflowX: "auto", margin: "10px 0 16px", fontSize: 12, color: "#8b949e", fontFamily: '"SF Mono","Consolas",monospace', lineHeight: 1.6 }}>{children}</pre>;
}
function Term({ name, hindi, children }) {
  return (
    <div style={{ background: "#0d1117", border: "1px solid #30363d", borderLeft: "4px solid #388bfd", borderRadius: 6, padding: "14px 16px", margin: "12px 0" }}>
      <div style={{ fontWeight: 700, fontSize: 14, color: "#e6edf3", marginBottom: 3 }}>{name}</div>
      {hindi && <div style={{ fontSize: 11, color: "#d29922", marginBottom: 8, fontStyle: "italic" }}>{hindi}</div>}
      <div style={{ fontSize: 12, color: "#8b949e", lineHeight: 1.7 }}>{children}</div>
    </div>
  );
}
function Pill({ color, children }) {
  const colors = { green: ["#0d4429","#3fb950"], red: ["#2d1b1b","#f85149"], yellow: ["#2d2a1b","#d29922"], blue: ["#1c3053","#58a6ff"] };
  const [bg, fg] = colors[color] || colors.blue;
  return <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600, background: bg, color: fg }}>{children}</span>;
}
function Note({ children }) {
  return <div style={{ background: "#1c3053", border: "1px solid #388bfd", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "#8b949e", margin: "12px 0", lineHeight: 1.7 }}><strong style={{ color: "#58a6ff" }}>Note: </strong>{children}</div>;
}
function Warn({ children }) {
  return <div style={{ background: "#2d2a1b", border: "1px solid #d29922", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "#8b949e", margin: "12px 0", lineHeight: 1.7 }}><strong style={{ color: "#d29922" }}>⚠️ </strong>{children}</div>;
}
function Table({ heads, rows }) {
  return (
    <div style={{ overflowX: "auto", margin: "12px 0 16px" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr>{heads.map(h => <th key={h} style={{ textAlign: "left", padding: "8px 10px", color: "#8b949e", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: "1px solid #30363d" }}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j} style={{ padding: "8px 10px", borderBottom: "1px solid #21262d", color: "#e6edf3", verticalAlign: "top" }}>{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const sidebar = [
  { section: "Introduction", items: [["intro","Yeh App Kya Hai"],["arch","Architecture"]] },
  { section: "Trading Terms", items: [["terms","Full Glossary"],["premium","Premium vs Risk"],["sl-buffer","SL Buffer Logic"]] },
  { section: "Strategy", items: [["ema-strategy","8-30 EMA Strategy"],["filters","Filter System"],["oi-section","OI / Support / Resistance"],["example","Full Example"]] },
  { section: "API Reference", items: [["backend-api","Backend API Map"],["third-party","Third-Party APIs"]] },
  { section: "How It Runs", items: [["server-start","Server Start Flow"],["kite-flow","Kite Token Flow"],["algo-flow","Algo Runner Flow"]] },
  { section: "Data", items: [["trade-fields","Trade Object Fields"],["why-values","Why These Values?"]] },
];

export default function Docs() {
  const scroll = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <div className="container">
      <div className="docs-layout">
        {/* Sidebar */}
        <div className="docs-sidebar">
          {sidebar.map(({ section, items }) => (
            <div key={section}>
              <div className="docs-sidebar-title">{section}</div>
              {items.map(([id, label]) => (
                <a key={id} className="docs-link" href={`#${id}`}
                  onClick={e => { e.preventDefault(); scroll(id); }}>{label}</a>
              ))}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="docs-content">
          <h1 id="intro" style={{ fontSize: 22, fontWeight: 700, color: "#58a6ff", marginBottom: 6 }}>8-30 EMA Algo — Full Guide</h1>
          <P>Hinglish mein — architecture se leke live trading tak, sab kuch.</P>

          <P>
            Yeh project ek <strong style={{color:"#e6edf3"}}>NIFTY/BANKNIFTY options algo dashboard + paper trading system</strong> hai.
            Backend Flask API chalata hai, frontend React dashboard us API ko hit karta hai, aur local algo runner market data dekh kar paper trades create karta hai.
            Strategy ka base <strong style={{color:"#e6edf3"}}>8 EMA aur 30 EMA</strong> hai: fast EMA trend ko jaldi pakadta hai, slow EMA broad direction batata hai.
          </P>
          <Note>SELL direction ka matlab option short/sell karna nahi hai. SELL ka matlab market bearish signal hai, isliye algo PE buy karta hai. BUY signal par CE buy hota hai. Dono cases me option buy hota hai.</Note>

          <H2 id="arch">Big Picture Architecture</H2>
          <P>System ko 4 layers me samjho:</P>
          <Table
            heads={["Layer", "File / Service", "Kaam"]}
            rows={[
              ["Frontend", "frontend/src/*", "Dashboard UI, auth screen, settings, Kite tab, charts, trades table"],
              ["Backend", "backend/app.py", "Flask app, CORS, blueprints register, startup"],
              ["Auth", "routes/auth.py + services/auth_service.py", "Login, bcrypt password hash, JWT token, protected routes"],
              ["Kite", "routes/kite.py + services/kite_service.py", "Kite login URL, request_token → access_token, status"],
              ["Market", "routes/market.py + services/market_service.py", "VIX, OI, candles, algo status, logs"],
              ["Trades", "routes/trades.py + services/trade_service.py", "Trades, summary, equity curves, daily history"],
              ["Database", "core/database.py", "MongoDB collections: trades, users, logs, kite_creds, app_config, daily_summary"],
            ]}
          />

          <H2 id="terms">Trading Terms — Full Glossary</H2>
          <Table
            heads={["Term", "Full Form", "Meaning + Project Use"]}
            rows={[
              ["NIFTY", "Nifty 50 Index", "NSE ke top 50 stocks ka index. Default instrument."],
              ["BANKNIFTY", "Nifty Bank Index", "Banking stocks ka index. Settings me choose kar sakte ho."],
              ["NSE / NFO", "National Stock Exchange / Futures & Options", "Market, option chain, holidays, VIX aur NFO instruments."],
              ["Spot", "Index spot price", "Actual NIFTY price. Strategy levels spot par bante hain."],
              ["OHLC", "Open High Low Close", "Candle ka data: first, highest, lowest, last price."],
              ["CE", "Call Option", "Market upar jaye to premium badhta hai. BUY signal me CE buy."],
              ["PE", "Put Option", "Market neeche jaye to premium badhta hai. SELL signal me PE buy."],
              ["ATM", "At The Money", "Current spot ke sabse paas strike. NIFTY 24345 → ATM 24350."],
              ["LTP", "Last Traded Price", "Option ka current premium. Entry ke liye use."],
              ["Bid / Ask", "—", "Bid = buyer price. Ask = seller price. Spread = Ask − Bid."],
              ["OI", "Open Interest", "Open option contracts. Support/resistance wall detect karne ke liye."],
              ["PCR", "Put Call Ratio", "Total PE OI / Total CE OI. Bias label ke liye."],
              ["VIX", "Volatility Index", "Market fear gauge. High VIX me size reduce/skip."],
              ["EMA", "Exponential Moving Average", "Recent price ko zyada weight dene wala average."],
              ["ADX", "Average Directional Index", "Trend strength. ADX < 20 means sideways, skip."],
              ["SL", "Stop Loss", "Wrong trade me exit level. Loss control."],
              ["RR", "Risk Reward", "1:2 ka matlab 1 risk pe 2 reward target."],
              ["EOD", "End Of Day", "Market close ke paas open trades force close hoti hain."],
              ["JWT", "JSON Web Token", "Login ke baad frontend ko token milta hai, protected APIs me use."],
            ]}
          />

          <H2 id="premium">Premium, Lot Size, Cost vs Risk</H2>
          <P>Option premium per unit quote hota hai, lekin trade lot me hota hai.</P>
          <Pre>{`1 lot cost  = option premium × lot size = 208.6 × 65 = ₹13,559
Risk per lot = option SL gap × lot size  =   7.5 × 65 = ₹487.5

Risk allowed = 55,000 × 1.5% = ₹825
Lots         = 825 / 487.5   = 1 lot`}</Pre>
          <Warn>Total cost aur risk ko same mat samjho. Cost = premium block; Risk = stop loss hit hone par expected loss.</Warn>

          <H2 id="sl-buffer">SL Buffer Logic — Kyun 15 Points?</H2>
          <P>Strategy spot candles par signal banati hai. Spot SL ko option SL me convert karne ke liye delta ≈ 0.5 use hota hai.</P>
          <Table
            heads={["SL_BUFFER", "Option Gap", "Entry ₹208.6 par SL", "Matlab"]}
            rows={[
              ["2 pts", "2×0.5 = ₹1", "₹207.6", "Bahut tight — normal noise me hit"],
              ["8 pts", "8×0.5 = ₹4", "₹204.6", "Still tight"],
              ["15 pts", "15×0.5 = ₹7.5", "₹201.1", "✓ Recommended — breathing room milti hai"],
            ]}
          />

          <H2 id="ema-strategy">Strategy Logic — 8 EMA / 30 EMA</H2>
          <P>EMA8 &gt; EMA30 → Bullish → ATM CE buy. EMA8 &lt; EMA30 → Bearish → ATM PE buy.</P>
          <Table
            heads={["Signal", "Condition", "Entry", "SL", "RR"]}
            rows={[
              ["Retest BUY",      "EMA8>EMA30, price EMA30 ke paas, bullish dominance/rejection candle", "Candle high + 0.5", "Candle low − 15pts", "1:3"],
              ["Retest SELL",     "EMA8<EMA30, price EMA30 ke paas, bearish candle",                    "Candle low − 0.5",  "Candle high + 15pts", "1:3"],
              ["Continuation BUY","EMA gap stretched, bullish dominance candle",                         "Candle high + 0.5", "Candle low − 15pts", "1:2"],
              ["Continuation SELL","EMA gap stretched, bearish dominance candle",                        "Candle low − 0.5",  "Candle high + 15pts", "1:2"],
            ]}
          />
          <Note>Retest ko 1:3 diya — setup cleaner hai: trend + pullback + confirmation. Continuation ko 1:2 — market already move kar chuka hota hai.</Note>

          <H2 id="filters">Filter System — Algo Kab Skip Karta Hai</H2>
          <Table
            heads={["Filter", "Value / Rule", "Action", "Reason"]}
            rows={[
              ["ADX", "< 20", <Pill color="red">Skip signal</Pill>, "Sideways market me EMA false signals high"],
              ["VIX", "20–25", <Pill color="yellow">50% qty</Pill>, "Volatility elevated, risk reduce"],
              ["VIX", "≥ 25", <Pill color="red">No trade</Pill>, "Premiums expensive/noisy"],
              ["Opening window", "9:15–9:45", <Pill color="yellow">Pause</Pill>, "Opening fake moves avoid"],
              ["Late day", "> 3:00 PM", <Pill color="red">No new entry</Pill>, "Late-day risk avoid"],
              ["EOD close", "3:20 PM", <Pill color="red">Force close</Pill>, "Overnight option risk avoid"],
              ["OI wall", "Within 50 pts", <Pill color="red">Block entry</Pill>, "Support/resistance ke saamne entry avoid"],
              ["Liquidity", "Volume<100 or OI<500", <Pill color="red">Skip option</Pill>, "Illiquid option me bad fill"],
              ["Max trades", "3/day", <Pill color="red">Block order</Pill>, "Overtrading avoid"],
              ["Daily loss", "≥ ₹2,000", <Pill color="red">Stop for day</Pill>, "Bad day stop"],
              ["Capital cap", "30% per trade", <Pill color="yellow">Reduce lots</Pill>, "Overleveraging avoid"],
            ]}
          />

          <H2 id="oi-section">OI, Support, Resistance, PCR, Max Pain</H2>
          <P>OI = option market me kitne contracts open hain. High CE OI = resistance wall. High PE OI = support wall.</P>
          <P>Code current spot ke around strikes scan karta hai, nearest usable expiry select karta hai, PCR = total PE OI / total CE OI. Max pain approximate strike bhi calculate hoti hai.</P>
          <Note>OI_BUFFER = 50 kyunki NIFTY strikes 50 point gap par hote hain. Agar price max OI wall se 50 point ke andar hai, to target hit hone se pehle wall reaction aa sakta hai.</Note>

          <H2 id="example">Full Example — Numbers Ke Saath</H2>
          <P>NIFTY bullish: EMA8 &gt; EMA30, ADX 24, bullish dominance candle, price EMA30 ke paas retest. Retest BUY signal banta hai.</P>
          <Pre>{`Option premium = ₹208.6  |  Lot size = 65  |  1 lot cost = ₹13,559

SL_BUFFER = 15pts, delta ≈ 0.5
Option SL gap = 15 × 0.5 = ₹7.5
Option SL     = 208.6 − 7.5 = ₹201.1
Risk per lot  = 7.5 × 65 = ₹487.5

Risk allowed = 55,000 × 1.5% = ₹825
Lots = 825 / 487.5 = 1 lot ✓

RR 1:3 → option target gap = 15×3×0.5 = ₹22.5
Option target = 208.6 + 22.5 = ₹231.1
Reward if target hit = 22.5 × 65 = ₹1,462.5`}</Pre>

          <H2 id="backend-api">Backend API — Full Map</H2>
          <Table
            heads={["Method + URL", "Auth", "Response", "Use"]}
            rows={[
              ["POST /api/auth/login", "No", '{"status":"ok","token":"JWT","username":"..."}', "Login — token localStorage me save"],
              ["GET /api/summary", "Bearer", '{"all":{...},"today":{...}}', "Dashboard summary cards"],
              ["GET /api/trades", "Bearer", "Array of trade objects", "Trades table"],
              ["GET /api/equity", "Bearer", '[{"x":"Start","y":55000},...]', "All-time equity chart"],
              ["GET /api/todays_equity", "Bearer", "Same, today only", "Today chart"],
              ["GET /api/daily_history", "Bearer", "Array of daily summaries", "Daily history"],
              ["GET /api/settings", "Bearer", "All trading settings", "Settings screen"],
              ["POST /api/settings", "Bearer", '{"status":"saved"}', "Update settings"],
              ["POST /api/mongo/connect", "Bearer", '{"status":"connected"}', "Runtime MongoDB connect"],
              ["GET /api/mongo/status", "Bearer", '{"connected":true/false}', "Mongo badge"],
              ["GET /api/vix", "Bearer", '{"vix":18.2,"status":"NORMAL"}', "VIX card"],
              ["GET /api/oi", "Bearer", "support, resistance, max_pain, pcr, expiry, bias", "OI levels card"],
              ["GET /api/candles", "Bearer", '[{"t":"09:20","o":...,"ema8":...}]', "Candle chart"],
              ["GET /api/status", "Bearer", '{"running":true,"last_log":"..."}', "Algo running badge"],
              ["GET /api/logs?date=YYYY-MM-DD", "Bearer", '{"lines":[...],"source":"mongodb"}', "Logs panel"],
              ["POST /api/kite/login-url", "Bearer", '{"login_url":"https://kite..."}', "Kite login link"],
              ["POST /api/kite/generate-token", "Bearer", '{"status":"connected","user":"..."}', "Token exchange"],
              ["GET /api/kite/status", "Bearer", '{"connected":true,"date":"..."}', "Kite status"],
            ]}
          />

          <H2 id="third-party">Third-Party APIs</H2>
          <Table
            heads={["System", "Method / URL", "Data", "Code"]}
            rows={[
              ["Zerodha Kite", "KiteConnect(api_key).login_url()", "Login URL string", "kite_service.get_login_url"],
              ["Zerodha Kite", "kite.generate_session(request_token, api_secret)", "access_token, user_name", "kite_service.generate_token"],
              ["Zerodha Kite", "kite.instruments('NSE')", "NSE instrument list with tokens", "algo_trader.get_index_token"],
              ["Zerodha Kite", "kite.instruments('NFO')", "Options master: strike, expiry, lot_size, token", "option_chain — ATM select, OI scan"],
              ["Zerodha Kite", "kite.historical_data(...)", "Candles: date, open, high, low, close, volume", "algo_trader.fetch_candles"],
              ["Zerodha Kite", "kite.quote(['NFO:symbol'])", "last_price, oi, volume, depth", "option entry/exit price"],
              ["NSE", "nseindia.com/api/allIndices", "INDIA VIX row with last value", "iv_filter.fetch_india_vix"],
              ["NSE", "nseindia.com/api/event-calendar", "Event items with date/purpose", "news_filter — high-impact event check"],
              ["RBI", "rbi.org.in/scripts/rss.aspx", "RSS headlines", "news_filter — RBI policy/rate check"],
              ["CallMeBot", "api.callmebot.com/whatsapp.php?...", "Success/fail text", "report._send_whatsapp — optional alerts"],
              ["MongoDB", "MongoClient ping / find / update_one", "Trades, users, creds, config, logs", "core/database.py"],
            ]}
          />
          <Warn>NSE free endpoints kabhi-kabhi fail/rate-limit ho sakte hain. Code VIX/OI failure par UNKNOWN/{} return karta hai so dashboard crash na ho.</Warn>

          <H2 id="server-start">Server Start Flow</H2>
          <P>Local command <Code>python app.py</Code> chalane par:</P>
          <ol style={{ fontSize: 13, color: "#8b949e", paddingLeft: 20, lineHeight: 2.2 }}>
            <li>config.py — .env load: MONGO_URL, KITE keys, FRONTEND_URL, JWT_SECRET</li>
            <li>db.connect(MONGO_URL) — Mongo ping, algo_trader database select</li>
            <li>Indexes ensure: trades, daily_summary, logs, users (unique username)</li>
            <li>Kite creds MongoDB se restore → config me set</li>
            <li>Users empty → frontend register screen dikhata hai</li>
            <li>Server port: env PORT ya fallback 4200</li>
          </ol>
          <Note>Gunicorn (Railway deploy) me _startup() auto-call nahi hota — sirf __main__ block me hai. Production me MongoDB MONGO_URL env var se auto-connect hota hai via config.</Note>

          <H2 id="kite-flow">Kite Token Flow — Request Token Se Access Token Tak</H2>
          <ol style={{ fontSize: 13, color: "#8b949e", paddingLeft: 20, lineHeight: 2.2 }}>
            <li>User Kite tab me API key/secret enter karta hai (ya .env se auto-detect)</li>
            <li>Frontend POST /api/kite/login-url hit karta hai</li>
            <li>Backend KiteConnect(api_key).login_url() se login link banata hai</li>
            <li>User Zerodha browser login karta hai — redirect URL me request_token milta hai</li>
            <li>Frontend POST /api/kite/generate-token par request_token bhejta hai</li>
            <li>Backend kite.generate_session(request_token, api_secret) call karta hai</li>
            <li>access_token MongoDB kite_creds collection me save hota hai</li>
            <li>Local algo runner zerodha_login.get_kite() se same-day token read karke Kite instance banata hai</li>
          </ol>

          <H2 id="algo-flow">Algo Runner Flow — Subah Se EOD Tak</H2>
          <ol style={{ fontSize: 13, color: "#8b949e", paddingLeft: 20, lineHeight: 2.2 }}>
            <li>Start: Kite authenticated object banta hai, paper_trade engine ko Kite inject hota hai</li>
            <li>Index token lookup: NIFTY/BANKNIFTY instrument token milta hai</li>
            <li>Pre-market: holiday/news/RBI/VIX/OI checks</li>
            <li>09:15 tak wait; 09:15–09:45 pause (opening volatility)</li>
            <li>Candle fetch: Kite historical_data se latest 5-min candles</li>
            <li>Indicators: EMA8, EMA30, ADX, direction, stretched calculate</li>
            <li>Existing open trade check: spot SL/target trigger check; exit price live LTP se</li>
            <li>New signal: detect_signal — all filters run</li>
            <li>OI alignment: wall ke paas block</li>
            <li>ATM CE/PE select — LTP/bid/ask/OI/volume/lot_size fetch</li>
            <li>SL/target conversion: spot gap × delta 0.5</li>
            <li>Lots: risk amount ÷ risk per lot, VIX multiplier, capital cap apply</li>
            <li>Paper order: OPEN state me save + log</li>
            <li>Exit: TARGET_HIT / SL_HIT / CLOSED_EOD; PnL = (exit − entry) × qty</li>
            <li>15:20 EOD: all open trades close, daily summary MongoDB me save</li>
          </ol>

          <H2 id="trade-fields">Trade Object Fields</H2>
          <Table
            heads={["Field", "Meaning"]}
            rows={[
              ["symbol", "Option tradingsymbol, e.g. NIFTY26APR24550CE"],
              ["direction", "BUY = bullish CE setup | SELL = bearish PE setup"],
              ["entry_type", "Retest ya Continuation"],
              ["lots / qty", "Lots count aur total qty = lots × lot_size"],
              ["opt_type", "CE or PE"],
              ["spot_entry / spot_sl / spot_target", "Strategy ke index-level levels"],
              ["entry / sl / target", "Option premium-level levels"],
              ["rr", "Risk reward: Retest=3, Continuation=2"],
              ["ltp_at_entry", "Option LTP at entry time"],
              ["bid_at_entry / ask_at_entry", "Market depth first bid/ask at entry"],
              ["oi_at_entry / volume_at_entry", "Liquidity snapshot at entry"],
              ["total_cost", "entry premium × qty"],
              ["status", "OPEN | TARGET_HIT | SL_HIT | CLOSED_EOD"],
              ["pnl", "(exit_price − entry) × qty"],
              ["exit_price / exit_value", "Exit premium aur exit premium × qty"],
            ]}
          />

          <H2 id="why-values">Why These Values?</H2>
          <Term name="RISK_PCT = 1.5%" hindi="Per trade maximum risk percentage">
            ₹55,000 capital par ₹825 risk per trade. 3 trades worst case = ₹2,475, lekin daily loss limit ₹2,000 extra brake lagata hai. Aggressive nahi, controlled.
          </Term>
          <Term name="MAX_CAPITAL_PER_TRADE = 30%" hindi="Ek trade me capital ka max portion">
            Kabhi-kabhi SL gap bahut tight hota hai aur formula lots ko bada kar sakta hai. Example: risk per lot ₹100 ho to ₹825 risk = 8 lots — premium cost bahut bada. Capital cap overleveraging rokta hai.
          </Term>
          <Term name="ADX Threshold = 20" hindi="Trend strength minimum">
            20 se neeche market choppy/sideways maana jaata hai. EMA strategy sideways me weak hoti hai — isliye filter zaroori hai.
          </Term>
          <Term name="OI_BUFFER = 50" hindi="OI wall se safe distance">
            NIFTY strikes 50 point gap par hote hain. Agar resistance/support wall ke 50 points ke andar entry hai, to trade clean space nahi milta.
          </Term>
          <Term name="SL_BUFFER = 15" hindi="Candle low/high se extra cushion">
            NIFTY ATM option me normal fluctuation ₹3–₹5 ho sakti hai. 2–8 point buffer option me ₹1–₹4 gap = trade random noise me cut hoga. 15 points = ₹7.5 gap = breathing room.
          </Term>

          <div style={{ background: "#2d1b1b", border: "1px solid #b91c1c", borderRadius: 8, padding: "16px 20px", marginTop: 24 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#f85149", marginBottom: 8 }}>⚠️ Disclaimer</div>
            <div style={{ fontSize: 12, color: "#8b949e", lineHeight: 1.8 }}>
              Yeh project documentation hai, financial advice nahi. Live trading se pehle paper trading results, broker charges, slippage, internet failures, Kite token expiry aur order execution risk samjho. Saari responsibility trader ki hai.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
