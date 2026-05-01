function Step({ num, done, title, children }) {
  return (
    <div style={{ display: "flex", gap: 16, padding: "20px 0", borderBottom: "1px solid #21262d" }}>
      <div style={{
        width: 32, height: 32, borderRadius: "50%", flexShrink: 0, marginTop: 2,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 13, fontWeight: 700,
        background: done ? "#238636" : "#1f6feb", color: "#fff",
      }}>
        {done ? "✓" : num}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: "#e6edf3", marginBottom: 8 }}>{title}</div>
        <div style={{ fontSize: 13, color: "#8b949e", lineHeight: 1.9 }}>{children}</div>
      </div>
    </div>
  );
}

function Section({ title, children, color = "#58a6ff" }) {
  return (
    <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: "20px 24px", marginBottom: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 16, paddingBottom: 10, borderBottom: "1px solid #21262d" }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function Warn({ children }) {
  return (
    <div style={{ background: "#2d1b1b", border: "1px solid #d29922", borderLeft: "4px solid #d29922", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "#8b949e", margin: "12px 0", lineHeight: 1.8 }}>
      <strong style={{ color: "#d29922" }}>⚠️ </strong>{children}
    </div>
  );
}

function Info({ children }) {
  return (
    <div style={{ background: "#1c3053", border: "1px solid #388bfd", borderLeft: "4px solid #388bfd", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "#8b949e", margin: "12px 0", lineHeight: 1.8 }}>
      <strong style={{ color: "#58a6ff" }}>ℹ️ </strong>{children}
    </div>
  );
}

function Success({ children }) {
  return (
    <div style={{ background: "#0d4429", border: "1px solid #3fb950", borderLeft: "4px solid #3fb950", borderRadius: 6, padding: "10px 14px", fontSize: 12, color: "#8b949e", margin: "12px 0", lineHeight: 1.8 }}>
      <strong style={{ color: "#3fb950" }}>✓ </strong>{children}
    </div>
  );
}

function Code({ children }) {
  return <code style={{ fontFamily: '"SF Mono","Consolas",monospace', background: "#0d1117", border: "1px solid #30363d", borderRadius: 4, padding: "2px 6px", fontSize: 12, color: "#79c0ff" }}>{children}</code>;
}

function Pre({ children }) {
  return <pre style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 6, padding: "14px 16px", overflowX: "auto", margin: "10px 0", fontSize: 12, color: "#8b949e", fontFamily: '"SF Mono","Consolas",monospace', lineHeight: 1.6 }}>{children}</pre>;
}

export default function GoLive() {
  return (
    <div className="container" style={{ maxWidth: 860 }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: "#f0883e", marginBottom: 6 }}>🚀 Paper se Real Money — Step by Step Guide</h2>
        <p style={{ fontSize: 13, color: "#8b949e" }}>
          Yeh guide tumhe paper trading se live real-money trading tak le jaayegi. Har step carefully follow karo — ek baar live mode me galti ka matlab real money ka loss hai.
        </p>
      </div>

      <Warn>
        <strong>Pehle yeh padhna zaroori hai:</strong> Real trading me slippage, brokerage charges, internet failure, token expiry, aur order rejection real risks hain. Sirf tab switch karo jab paper trading me consistent results ho — kam se kam 2–3 mahine, 60%+ win rate, aur daily loss limit kabhi hit na hui ho.
      </Warn>

      {/* ── PHASE 1 ── */}
      <Section title="Phase 1 — Zerodha Account Setup" color="#58a6ff">
        <Step num={1} title="Zerodha Account Open Karo (agar nahi hai)">
          <strong style={{ color: "#e6edf3" }}>zerodha.com</strong> par jaao → "Open an Account" → Aadhaar-based instant account.<br />
          Documents chahiye: PAN card, Aadhaar card, bank account details, signature, selfie.<br />
          Account usually <strong style={{ color: "#e6edf3" }}>1–2 business days</strong> me activate hota hai.
          <Info>F&O (Futures &amp; Options) trading ke liye Zerodha ko separately F&amp;O segment activate karna padta hai. Account open hone ke baad Kite app → Profile → Segments → F&amp;O enable karo. Agar income proof maange to ITR ya 6-month bank statement de sakte ho.</Info>
        </Step>

        <Step num={2} title="Zerodha Account Me Paise Daalo (Fund Your Account)">
          <strong style={{ color: "#e6edf3" }}>Kite app ya kite.zerodha.com</strong> → Funds → Add Funds.<br /><br />
          <strong style={{ color: "#e6edf3" }}>Minimum recommended for this algo:</strong><br />
          • Active capital: <strong style={{ color: "#3fb950" }}>₹55,000+</strong> (settings me jo set hai)<br />
          • Extra buffer: <strong style={{ color: "#3fb950" }}>₹10,000–₹15,000</strong> (margin aur charges ke liye)<br />
          • <strong style={{ color: "#e6edf3" }}>Total recommended: ₹70,000+</strong><br /><br />
          Payment methods: UPI (instant), NEFT/RTGS (same day), net banking.<br />
          <Warn>SEBI rules ke karan: equity funds T+1 din me available hote hain. Options trading ke liye funds usually same day available rahte hain agar UPI se add karo.</Warn>
        </Step>

        <Step num={3} title="F&O Margins Samjho">
          NIFTY options <strong style={{ color: "#e6edf3" }}>buy</strong> karne ke liye sirf premium amount chahiye (margin nahi).<br />
          1 lot NIFTY ATM option ≈ ₹150–₹250 premium × 75 = <strong style={{ color: "#e6edf3" }}>₹11,000–₹18,750</strong>.<br />
          Is algo me hum sirf options buy karte hain (sell/short nahi) — isliye margin requirement low hai.
          <Info>Zerodha ka SPAN margin calculator: <strong style={{ color: "#58a6ff" }}>zerodha.com/margin-calculator</strong> — wahan exact margin check kar sakte ho kisi bhi option ke liye.</Info>
        </Step>
      </Section>

      {/* ── PHASE 2 ── */}
      <Section title="Phase 2 — Kite Connect API Setup" color="#3fb950">
        <Step num={4} title="Zerodha Developer Console Par App Create Karo">
          <strong style={{ color: "#e6edf3" }}>developers.kite.trade</strong> jaao → Login with Zerodha → "Create New App" → Connect type choose karo.<br /><br />
          Form me fill karo:<br />
          • <strong style={{ color: "#e6edf3" }}>App Name:</strong> Kuch bhi (e.g. "My Algo Dashboard")<br />
          • <strong style={{ color: "#e6edf3" }}>Redirect URL:</strong> <Code>http://127.0.0.1:4200</Code> ← exactly yahi daalo<br />
          • <strong style={{ color: "#e6edf3" }}>Description:</strong> Kuch bhi<br /><br />
          Submit karo → <strong style={{ color: "#3fb950" }}>API Key aur API Secret milega</strong>. Inhe safely store karo.
          <Warn>Redirect URL exactly <Code>http://127.0.0.1:4200</Code> honi chahiye — port bhi same. Agar different daali to login flow kaam nahi karega.</Warn>
        </Step>

        <Step num={5} title="API Key aur Secret Backend .env Me Daalo">
          File: <Code>backend/.env</Code> open karo aur update karo:
          <Pre>{`KITE_API_KEY=tumhara_api_key_yahan
KITE_API_SECRET=tumhara_api_secret_yahan`}</Pre>
          Alternatively, Dashboard → Kite Connect tab → manually enter karo (MongoDB me save ho jaayega).
        </Step>

        <Step num={6} title="Daily Token Generate Karo (Har Subah)">
          Yeh step <strong style={{ color: "#f85149" }}>roz subah market open se pehle</strong> karna padta hai:<br /><br />
          1. Dashboard → Kite Connect tab → "Open Zerodha Login" button click karo<br />
          2. Browser me Zerodha login karo (user + password + TOTP/2FA)<br />
          3. Login ke baad redirect URL me <Code>request_token=XXXXXX</Code> dikhaai dega<br />
          4. Woh token copy karo aur dashboard me paste karo → "Connect Kite" click karo<br />
          5. <strong style={{ color: "#3fb950" }}>Connected</strong> badge dikhe → done!
          <Info>Access token sirf 1 din ke liye valid hota hai. Har roz subah yeh process repeat karna padega — approximately 2 minutes ka kaam hai.</Info>
        </Step>
      </Section>

      {/* ── PHASE 3 ── */}
      <Section title="Phase 3 — Paper se Real Me Switch Karna" color="#f0883e">
        <Step num={7} title="Settings Me Paper Trading Off Karo">
          Dashboard → Settings tab jaao:<br /><br />
          • <strong style={{ color: "#e6edf3" }}>Paper Trading:</strong> <Code>No — Real Orders ⚠️</Code> select karo<br />
          • <strong style={{ color: "#e6edf3" }}>Capital:</strong> Jo tumhare Zerodha account me available hai woh daalo<br />
          • <strong style={{ color: "#e6edf3" }}>Daily Loss Limit:</strong> Capital ka 3–4% recommended (e.g. ₹55,000 → ₹1,650–₹2,200)<br />
          • <strong style={{ color: "#e6edf3" }}>Max Trades/Day:</strong> Shuru me 2 rakhna safer hai<br /><br />
          "Save Settings" click karo.
          <Warn>Real mode me algo actual buy/sell orders Zerodha par place karega. Galat settings = real money loss. Double check karo.</Warn>
        </Step>

        <Step num={8} title="algo_trader.py Ka Real Order Code Enable Karo">
          Paper trading me <Code>paper_trade.py</Code> use hota hai jo fake trades log karta hai.<br />
          Real trading ke liye <Code>algo_trader.py</Code> me <Code>PAPER_TRADING = False</Code> set karo ya .env me:<br />
          <Pre>{`PAPER_TRADING=false`}</Pre>
          Phir algo start karo:
          <Pre>{`cd ~/Desktop/file/backend
source venv/bin/activate
python algo_trader.py`}</Pre>
        </Step>

        <Step num={9} title="First Live Day — Kya Dhyan Rakhna Hai">
          <strong style={{ color: "#e6edf3" }}>System monitor karo, especially:</strong><br />
          • Pehle trade ke time terminal me logs dekho — order placed ya rejected?<br />
          • Kite app par bhi order confirm karo (Orders tab)<br />
          • Zerodha Console → Orders me bhi check karo<br />
          • PnL dashboard par update ho rahi hai?
          <Info>Pehle 1–2 hafton me manually verify karo ki paper trading behavior aur real order behavior match kar raha hai. Koi bhi unexpected behavior par immediately algo stop karo — Ctrl+C ya process kill karo.</Info>
        </Step>
      </Section>

      {/* ── PHASE 4 ── */}
      <Section title="Phase 4 — Important Settings Checklist" color="#d29922">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[
            ["Zerodha Account", ["F&O segment enabled hai?", "Sufficient funds available hain?", "2FA (TOTP) setup hai?", "Bank account linked hai?"]],
            ["Kite API", ["API key aur secret .env me hai?", "Redirect URL exactly 127.0.0.1:4200 hai?", "Daily token generate hota hai?", "Kite Connected badge green hai?"]],
            ["Backend Settings", ["PAPER_TRADING=false set kiya?", "Capital correct amount hai?", "Daily loss limit 3–4% hai?", "Max trades 2–3 rakhna shuru me?"]],
            ["Safety Checks", ["MongoDB connected hai (data save hoga)?", "Internet stable hai trading hours me?", "Power backup hai (UPS/laptop)?", "Emergency me algo kaise stop karein pata hai?"]],
          ].map(([title, items]) => (
            <div key={title} style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 6, padding: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#e6edf3", marginBottom: 10 }}>{title}</div>
              {items.map(item => (
                <div key={item} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, color: "#8b949e", marginBottom: 6 }}>
                  <span style={{ color: "#d29922", flexShrink: 0 }}>□</span>{item}
                </div>
              ))}
            </div>
          ))}
        </div>
      </Section>

      {/* ── PHASE 5 ── */}
      <Section title="Phase 5 — Brokerage aur Charges Samjho" color="#58a6ff">
        <div style={{ fontSize: 13, color: "#8b949e", lineHeight: 1.9 }}>
          <strong style={{ color: "#e6edf3" }}>Zerodha Options Buying Charges (approximate):</strong><br /><br />

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, marginBottom: 16 }}>
              <thead>
                <tr>
                  {["Charge", "Rate", "1 Lot NIFTY Example (₹208 premium, 75 qty)"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 10px", color: "#8b949e", fontSize: 11, textTransform: "uppercase", borderBottom: "1px solid #30363d" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["Brokerage", "₹20 flat per order", "₹20 entry + ₹20 exit = ₹40"],
                  ["STT (buy side)", "0.0625% of premium", "0.000625 × ₹15,600 = ≈₹10"],
                  ["Exchange charges (NSE)", "0.053% of premium", "≈₹8"],
                  ["SEBI charges", "₹10 per crore", "negligible"],
                  ["GST (18%)", "On brokerage + exchange", "≈₹8–10"],
                  ["Stamp duty", "0.003% on buy side", "≈₹0.50"],
                  ["Total approx", "—", "₹65–₹80 round trip"],
                ].map((r, i) => (
                  <tr key={i}>
                    {r.map((c, j) => <td key={j} style={{ padding: "8px 10px", borderBottom: "1px solid #21262d", color: j === 2 ? "#e6edf3" : "#8b949e" }}>{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Info>Charges ko PnL calculation me include karo. ₹487.5 risk per lot hai, charges ₹70–₹80 hain — matlab effective risk ≈ ₹555–₹567 per trade. Daily loss limit accordingly thoda conservative rakho.</Info>

          <strong style={{ color: "#e6edf3" }}>Exact charges check karo:</strong> <strong style={{ color: "#58a6ff" }}>zerodha.com/charges</strong> ya Kite → Console → Reports → Tax P&L.
        </div>
      </Section>

      {/* ── PHASE 6 ── */}
      <Section title="Phase 6 — Emergency aur Safety Procedures" color="#f85149">
        <Step num={10} title="Algo Turant Kaise Band Karein">
          <strong style={{ color: "#e6edf3" }}>Option 1 — Terminal me:</strong> <Code>Ctrl + C</Code> — algo gracefully stop hoga<br /><br />
          <strong style={{ color: "#e6edf3" }}>Option 2 — Force kill:</strong>
          <Pre>{`# Mac/Linux
ps aux | grep algo_trader
kill -9 <PID>`}</Pre>
          <strong style={{ color: "#e6edf3" }}>Option 3 — Kite app se:</strong> Agar order place ho gaya hai par algo band nahi hua → Kite app → Orders → Open positions → Manually exit karo.
          <Warn>Algo band karne se open positions close nahi hoti. Zerodha Kite app par manually check karo ki koi open position toh nahi.</Warn>
        </Step>

        <Step num={11} title="Agar Internet Cut Ho Jaye Trading Hours Me">
          Open positions Zerodha server par hain — internet cut hone se trades effect nahi hote.<br />
          Lekin algo runner local machine par hai, isliye naya trade place nahi hoga aur existing trade ka SL/target monitor nahi hoga.<br /><br />
          <strong style={{ color: "#e6edf3" }}>Immediate steps:</strong><br />
          1. Mobile se Kite app open karo<br />
          2. Open positions check karo<br />
          3. Agar trade OPEN hai to manually close karo ya SL order place karo<br />
          4. Internet aane par algo restart karo (pehle token verify karo)
        </Step>

        <Step num={12} title="Daily Routine — Kya Kab Karna Hai">
          <div style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 6, padding: 16, marginTop: 8 }}>
            {[
              ["8:30 AM", "Backend start karo — python app.py"],
              ["8:45 AM", "Kite Connect tab → Token generate karo (roz naya)"],
              ["8:50 AM", "Dashboard check — MongoDB connected, Kite Connected, settings correct"],
              ["9:00 AM", "Algo start karo — python algo_trader.py"],
              ["9:15 AM", "Market open — algo pre-market checks run karega automatically"],
              ["9:15–3:20 PM", "Monitor karo — logs check, trades dekho, nothing manually do"],
              ["3:20 PM", "EOD — algo open trades close karega automatically"],
              ["3:30 PM", "Dashboard → Trade history check karo, PnL note karo"],
              ["3:35 PM", "Algo gracefully stop karo (Ctrl+C)"],
            ].map(([time, task]) => (
              <div key={time} style={{ display: "flex", gap: 16, padding: "8px 0", borderBottom: "1px solid #21262d", fontSize: 12 }}>
                <span style={{ color: "#58a6ff", fontWeight: 600, minWidth: 90, flexShrink: 0 }}>{time}</span>
                <span style={{ color: "#8b949e" }}>{task}</span>
              </div>
            ))}
          </div>
        </Step>
      </Section>

      {/* ── Final checklist ── */}
      <Section title="Final Go-Live Checklist" color="#3fb950">
        <Success>Paper trading me 2+ mahine consistent results — 60%+ win rate, daily loss limit kabhi hit nahi hui</Success>
        <Success>Zerodha account active, F&amp;O enabled, funds added (₹70,000+ recommended)</Success>
        <Success>Kite Connect API key + secret — developer console se liya, .env me save kiya</Success>
        <Success>Redirect URL exactly http://127.0.0.1:4200 set hai developer console me</Success>
        <Success>Daily token flow samajh gaye ho — roz 2 minute ka kaam hai</Success>
        <Success>PAPER_TRADING=false set kiya backend me</Success>
        <Success>Capital, daily loss limit, max trades settings verify kiye</Success>
        <Success>MongoDB connected hai — trades save honge</Success>
        <Success>Algo emergency stop procedure pata hai (Ctrl+C + Kite app se verify)</Success>
        <Success>Charges ka impact PnL expectation me account kiya</Success>

        <div style={{ background: "#0d4429", border: "1px solid #3fb950", borderRadius: 8, padding: "16px 20px", marginTop: 20, textAlign: "center" }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#3fb950", marginBottom: 6 }}>Sab check ✓ ? Ab Go Live karo!</div>
          <div style={{ fontSize: 12, color: "#8b949e" }}>Shubh labh — aur hamesha risk manage karo.</div>
        </div>
      </Section>
    </div>
  );
}
