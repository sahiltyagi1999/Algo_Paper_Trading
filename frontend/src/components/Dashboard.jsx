import EquityChart from "./EquityChart";
import CandleChart from "./CandleChart";
import TradesTable from "./TradesTable";

const fmt_inr = n => "₹" + parseFloat(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const fmt_pnl = n => {
  const a = Math.abs(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  return (n >= 0 ? "+" : "-") + "₹" + a;
};

function StatCard({ label, value, cls, sub }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className={`card-value ${cls || ""}`}>{value}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  );
}

function SectionLabel({ children }) {
  return <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.5px" }}>{children}</div>;
}

export default function Dashboard({ summary, equity, todayEquity, candles, vix, oi, trades, settings, onRefresh }) {
  const t = summary?.today || {};
  const a = summary?.all || {};
  const tp = t.total_pnl || 0;
  const ap = a.total_pnl || 0;

  const vixColors = { SAFE:"#3fb950", ELEVATED:"#d29922", HIGH:"#f0883e", DANGEROUS:"#f85149", UNKNOWN:"#8b949e", NORMAL:"#3fb950", VERY_LOW:"#3fb950" };
  const vixColor = vixColors[vix?.status] || "#8b949e";

  const bias = oi?.bias || "—";
  const biasColor = bias === "BULLISH" ? "#3fb950" : bias === "BEARISH" ? "#f85149" : "#8b949e";

  return (
    <div className="container">
      <SectionLabel>Today</SectionLabel>
      <div className="stats-grid">
        <StatCard label="Daily PnL"    value={fmt_pnl(tp)} cls={tp >= 0 ? "green" : "red"} />
        <StatCard label="Trades"       value={t.total_trades ?? "—"} cls="blue" />
        <StatCard label="Wins"         value={t.wins ?? "—"} cls="green" />
        <StatCard label="Losses"       value={t.losses ?? "—"} cls="red" />
        <StatCard label="Win Rate"     value={`${t.win_rate ?? "—"}%`} cls="yellow" />
        <StatCard label="Open Trades"  value={t.open_trades ?? "—"} cls="blue" />
      </div>

      <SectionLabel>All Time</SectionLabel>
      <div className="stats-grid">
        <StatCard label="Active Capital" value={fmt_inr(a.capital || 0)} cls="blue" sub="Trading on this" />
        <StatCard label="Profit Vault"   value={fmt_inr(a.profit_vault || 0)} cls="green" sub="Locked — not used" />
        <StatCard label="Total Wealth"   value={fmt_inr(a.total_wealth || 0)} cls="yellow" sub="Capital + Vault" />
        <StatCard label="Total PnL"      value={fmt_pnl(ap)} cls={ap >= 0 ? "green" : "red"} />
        <StatCard label="Total Trades"   value={a.total_trades ?? "—"} cls="blue" />
        <StatCard label="Win Rate"       value={`${a.win_rate ?? "—"}%`} cls="yellow" />
        <StatCard label="Total Wins"     value={a.wins ?? "—"} cls="green" />
        <StatCard label="Total Losses"   value={a.losses ?? "—"} cls="red" />
      </div>

      <div className="charts-row">
        <EquityChart data={equity} title="Equity Curve (All Time)" />
        <EquityChart data={todayEquity} title="Today's Performance" />
      </div>

      {candles?.length > 0 && (
        <CandleChart data={candles} instrument={settings?.instrument} />
      )}

      <div className="info-row">
        {/* OI Levels */}
        <div className="info-card">
          <div className="info-title">OI Levels ({settings?.instrument || "NIFTY"})</div>
          {[
            ["Support",    oi?.support,    "green"],
            ["Resistance", oi?.resistance, "red"],
            ["Max Pain",   oi?.max_pain,   "yellow"],
            ["PCR",        oi?.pcr,        ""],
            ["Expiry",     oi?.expiry,     ""],
          ].map(([label, val, cls]) => (
            <div className="level-row" key={label}>
              <span className="level-label">{label}</span>
              <span className={`level-value ${cls}`}>{val || "—"}</span>
            </div>
          ))}
          <div className="level-row">
            <span className="level-label">Bias</span>
            <span className="level-value" style={{ color: biasColor }}>{bias} (PCR)</span>
          </div>
        </div>

        {/* VIX */}
        <div className="info-card">
          <div className="info-title">India VIX</div>
          <div style={{ textAlign: "center", padding: "10px 0" }}>
            <div style={{ fontSize: 42, fontWeight: 700, color: vixColor }}>{vix?.vix ? vix.vix.toFixed(2) : "—"}</div>
            <div style={{ fontSize: 13, marginTop: 4, color: vixColor }}>{vix?.status || "Loading..."}</div>
            <div className="vix-meter" style={{ marginTop: 16 }}>
              <div className="vix-fill" style={{ width: `${Math.min(((vix?.vix || 0) / 40) * 100, 100)}%`, background: vixColor }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#8b949e", marginTop: 4 }}>
              <span>0</span><span>Safe &lt;15</span><span>High &gt;25</span><span>40</span>
            </div>
          </div>
        </div>

        {/* Strategy Config */}
        <div className="info-card">
          <div className="info-title">Strategy Config</div>
          {[
            ["Instrument",    settings?.instrument,                                                  "blue"],
            ["Active Capital",fmt_inr(settings?.capital || 0),                                       ""],
            ["Profit Vault",  fmt_inr(settings?.profit_vault || 0),                                  "green"],
            ["Risk/Trade",    `${((settings?.risk_pct || 0.015)*100).toFixed(1)}% = ${fmt_inr((settings?.capital || 0) * (settings?.risk_pct || 0.015))}`, "yellow"],
            ["Max Trades/Day",settings?.max_trades_day,                                              ""],
            ["Daily Loss Limit",fmt_inr(settings?.daily_loss_limit || 0),                           "red"],
            ["Timeframe",     "5 min",                                                               ""],
          ].map(([label, val, cls]) => (
            <div className="level-row" key={label}>
              <span className="level-label">{label}</span>
              <span className={`level-value ${cls}`}>{val ?? "—"}</span>
            </div>
          ))}
        </div>
      </div>

      <TradesTable trades={trades || []} onRefresh={onRefresh} />
    </div>
  );
}
