import { useState, useEffect } from "react";
import { api } from "../api/client";
import { useToast } from "./Toast";

export default function Settings() {
  const toast = useToast();
  const [mongoUrl, setMongoUrl] = useState("");
  const [mongoOk, setMongoOk] = useState(false);
  const [mongoDb, setMongoDb] = useState("");
  const [form, setForm] = useState({
    instrument: "NIFTY", paper_trading: "true", capital: 55000,
    profit_vault: 47000, daily_loss_limit: 2000, max_trades_day: 3,
    risk_pct: 0.015, ema_fast: 8, ema_slow: 30, adx_threshold: 20,
    sl_buffer: 15, oi_buffer: 50, square_off_time: "15:15",
  });

  async function load() {
    try {
      const [d, m] = await Promise.all([api.get("/api/settings"), api.get("/api/mongo/status")]);
      setForm({
        instrument:       d.instrument      || "NIFTY",
        paper_trading:    d.paper_trading   ? "true" : "false",
        capital:          d.capital         || 55000,
        profit_vault:     d.profit_vault    || 47000,
        daily_loss_limit: d.daily_loss_limit|| 2000,
        max_trades_day:   d.max_trades_day  || 3,
        risk_pct:         d.risk_pct        || 0.015,
        ema_fast:         d.ema_fast        || 8,
        ema_slow:         d.ema_slow        || 30,
        adx_threshold:    d.adx_threshold   || 20,
        sl_buffer:        d.sl_buffer       || 15,
        oi_buffer:        d.oi_buffer       || 50,
        square_off_time:  d.square_off_time || "15:15",
      });
      setMongoOk(m.connected);
      setMongoDb(m.db || "");
    } catch (e) { toast("Settings load error", "error"); }
  }

  useEffect(() => { load(); }, []);

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.value })); }

  async function connectMongo() {
    if (!mongoUrl.trim()) { toast("MongoDB URL enter karo", "error"); return; }
    const d = await api.post("/api/mongo/connect", { mongo_url: mongoUrl.trim() });
    if (d.error) { toast("Connection failed: " + d.error, "error"); return; }
    toast("MongoDB connected! DB: " + (d.db || ""), "success");
    setMongoOk(true); setMongoDb(d.db || ""); setMongoUrl("");
  }

  async function save() {
    const data = {
      instrument:       form.instrument,
      paper_trading:    form.paper_trading === "true",
      capital:          parseFloat(form.capital)      || 0,
      profit_vault:     parseFloat(form.profit_vault) || 0,
      max_trades_day:   parseInt(form.max_trades_day) || 3,
      risk_pct:         parseFloat(form.risk_pct)     || 0.015,
      ema_fast:         parseInt(form.ema_fast)           || 8,
      ema_slow:         parseInt(form.ema_slow)           || 30,
      adx_threshold:    parseFloat(form.adx_threshold)    || 20,
      sl_buffer:        parseFloat(form.sl_buffer)        || 15,
      oi_buffer:        parseFloat(form.oi_buffer)        || 50,
      square_off_time:  form.square_off_time || "15:15",
    };
    const d = await api.post("/api/settings", data);
    d.status === "saved" ? toast("Settings saved!", "success") : toast("Error: " + JSON.stringify(d), "error");
  }

  const Field = ({ label, id, type="number", hint, children }) => (
    <div className="form-group">
      <label className="form-label">{label}</label>
      {children || <input type={type} value={form[id]} onChange={set(id)} />}
      {hint && <div className="form-hint">{hint}</div>}
    </div>
  );

  return (
    <div className="container" style={{ maxWidth: 900 }}>
      <div style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#58a6ff", marginBottom: 4 }}>Settings</h2>
          <p style={{ fontSize: 13, color: "#8b949e" }}>Changes MongoDB mein persist hote hain aur live config update hota hai.</p>
        </div>
        <button className="btn btn-primary" onClick={load}>🔄 Refresh</button>
      </div>

      <div className="settings-section">
        <div className="settings-section-title">MongoDB Connection</div>
        <div className="conn-status" style={{ marginBottom: 14 }}>
          <div className={`conn-dot ${mongoOk ? "green" : "red"}`} />
          <span style={{ color: mongoOk ? "#3fb950" : "#f85149" }}>
            {mongoOk ? `Connected${mongoDb ? ` — DB: ${mongoDb}` : ""}` : "Not connected — URL enter karo"}
          </span>
        </div>
        <div className="form-grid-2">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">MongoDB URL</label>
            <input type="password" value={mongoUrl} onChange={e => setMongoUrl(e.target.value)} placeholder="mongodb+srv://user:pass@cluster.mongodb.net/" />
            <div className="form-hint">Apna Atlas connection string yahan paste karo</div>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button className="btn btn-primary" style={{ width: "100%" }} onClick={connectMongo}>Connect MongoDB</button>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-section-title">Trading Settings</div>
        <div className="form-grid-3">
          <Field label="Instrument" id="instrument" hint="NIFTY ya BANKNIFTY">
            <select value={form.instrument} onChange={set("instrument")}>
              <option value="NIFTY">NIFTY</option>
              <option value="BANKNIFTY">BANKNIFTY</option>
            </select>
          </Field>
          <Field label="Paper Trading" id="paper_trading" hint="Shuru mein hamesha Paper rakhein">
            <select value={form.paper_trading} onChange={set("paper_trading")}>
              <option value="true">Yes — Paper (Safe)</option>
              <option value="false">No — Real Orders ⚠️</option>
            </select>
          </Field>
          <Field label="Timeframe (min)" id="timeframe" hint="Fixed at 5 min (strategy requirement)">
            <input type="text" value="5 min (fixed)" readOnly style={{ opacity: 0.5, cursor: "not-allowed" }} />
          </Field>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-section-title">Capital &amp; Risk Management</div>
        <div className="form-grid-3">
          <Field label="Active Capital (₹)" id="capital" hint="Suggested: savings ka 20–30%" />
          <Field label="Profit Vault (₹)" id="profit_vault" hint="Locked profit — trade nahi hoga" />
          <Field label="Max Trades / Day" id="max_trades_day" hint="Suggested: 3–5" />
          <Field label="Risk Per Trade (%)" id="risk_pct" hint="Suggested: 0.01–0.02" />
          <Field label="Daily Loss Limit (₹)" id="daily_loss_limit" hint={`Auto = capital × risk% × max trades = ₹${Math.round(parseFloat(form.capital||0) * parseFloat(form.risk_pct||0) * parseInt(form.max_trades_day||1))}`}>
            <input
              type="text"
              value={`₹${Math.round(parseFloat(form.capital||0) * parseFloat(form.risk_pct||0) * parseInt(form.max_trades_day||1)).toLocaleString("en-IN")}`}
              readOnly
              style={{ opacity: 0.7, cursor: "not-allowed", color: "#f0883e" }}
            />
          </Field>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-section-title">EMA Strategy Parameters</div>
        <div className="form-grid-3">
          <Field label="EMA Fast" id="ema_fast" hint="Default: 8" />
          <Field label="EMA Slow" id="ema_slow" hint="Default: 30" />
          <Field label="ADX Threshold" id="adx_threshold" hint="Suggested: 20–25" />
          <Field label="SL Buffer (pts)" id="sl_buffer" hint="Suggested: 10–20 pts" />
          <Field label="OI Buffer (pts)" id="oi_buffer" hint="Suggested: 30–75 pts" />
          <Field label="Square Off Time" id="square_off_time" type="time" hint="Open trades is time par close honge, e.g. 15:15" />
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <button className="btn btn-success" onClick={save}>💾 Save Settings</button>
        <button className="btn btn-ghost" onClick={load}>Reset to Saved Values</button>
      </div>
    </div>
  );
}
