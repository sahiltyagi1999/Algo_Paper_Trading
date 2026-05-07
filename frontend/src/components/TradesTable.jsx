import { useEffect, useState } from "react";
import { api } from "../api/client";

const fmt_inr = n => "₹" + parseFloat(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const fmt_money = n => {
  const val = parseFloat(n || 0);
  return (val >= 0 ? "+₹" : "-₹") + Math.abs(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
};
const fmt_premium = n => {
  const val = parseFloat(n || 0);
  return (val >= 0 ? "+₹" : "-₹") + Math.abs(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
};

function CloseTradePanel({ trade, onClosed }) {
  const liveLtp = parseFloat(trade.live_ltp || 0);
  const [exitPrice, setExitPrice] = useState(liveLtp > 0 ? String(liveLtp) : "");
  const [userEdited, setUserEdited] = useState(false);
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [err, setErr]             = useState("");

  useEffect(() => {
    if (!userEdited && liveLtp > 0) {
      setExitPrice(String(liveLtp));
    }
  }, [liveLtp, userEdited]);

  async function handleClose() {
    setLoading(true);
    setErr("");
    setResult(null);
    try {
      let body = {};
      if (exitPrice.trim()) {
        const parsed = parseFloat(exitPrice);
        if (isNaN(parsed) || parsed <= 0) {
          setErr("Valid exit price enter karo (e.g. 185.5)");
          setLoading(false);
          return;
        }
        body = { exit_price: parsed };
      }
      const res  = await api.post(`/api/trades/${trade.trade_id}/close`, body);
      setResult(res);
      onClosed();
    } catch (e) {
      setErr(e?.message || "Close failed");
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    const pnl = parseFloat(result.pnl);
    return (
      <div style={{ marginTop: 12, padding: "10px 14px", background: "#0d1117", borderRadius: 6, border: "1px solid #30363d" }}>
        <div style={{ color: "#3fb950", fontWeight: 700, marginBottom: 4 }}>Trade Closed ✓</div>
        <div style={{ fontSize: 12, color: "#8b949e" }}>
          Exit @ ₹{parseFloat(result.exit_price).toLocaleString("en-IN")} &nbsp;|&nbsp;
          PnL: <span style={{ color: pnl >= 0 ? "#3fb950" : "#f85149", fontWeight: 700 }}>
            {pnl >= 0 ? "+" : ""}₹{pnl.toLocaleString("en-IN")}
          </span>
          &nbsp;|&nbsp; Mode: {result.mode}
          {result.kite_order_id && <>&nbsp;|&nbsp; Order ID: {result.kite_order_id}</>}
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginTop: 12, padding: "10px 14px", background: "#160d0d", borderRadius: 6, border: "1px solid #6e2020" }}>
      <div style={{ color: "#f85149", fontWeight: 700, marginBottom: 8, fontSize: 13 }}>
        ⚠ Close This Trade Now
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <input
          type="number"
          value={exitPrice}
          onChange={e => { setUserEdited(true); setExitPrice(e.target.value); }}
          placeholder="Auto live LTP"
          style={{
            background: "#0d1117", border: "1px solid #30363d", borderRadius: 4,
            color: "#e6edf3", padding: "5px 10px", fontSize: 12, width: 210,
          }}
        />
        <button
          onClick={handleClose}
          disabled={loading}
          style={{
            background: loading ? "#444" : "#b91c1c", color: "#fff", border: "none",
            borderRadius: 4, padding: "6px 16px", fontWeight: 700, fontSize: 12,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Closing…" : "Close Trade"}
        </button>
        <span style={{ fontSize: 11, color: "#8b949e" }}>
          {trade.symbol} · Qty {trade.qty}
          {liveLtp > 0 && <> · Live ₹{liveLtp.toLocaleString("en-IN")}</>}
        </span>
      </div>
      {err && <div style={{ color: "#f85149", fontSize: 12, marginTop: 6 }}>{err}</div>}
      <div style={{ fontSize: 11, color: "#6e7681", marginTop: 6 }}>
        Price auto-fills from live Kite LTP. You can override it manually if needed.
      </div>
    </div>
  );
}

function TradeRow({ t, idx, onRefresh }) {
  const [open, setOpen] = useState(false);
  const dir = t.direction || "", result = t.status || "OPEN";
  const isOpen = result === "OPEN";
  const livePnl = parseFloat(t.live_pnl || 0);
  const bookedPnl = parseFloat(t.pnl || 0);
  const pnl = isOpen && t.live_pnl !== undefined ? livePnl : bookedPnl;
  const entry  = parseFloat(t.entry_spot   || t.entry  || 0);
  const sl     = parseFloat(t.sl_spot      || t.sl     || 0);
  const target = parseFloat(t.target_spot  || t.target || 0);
  const optLtp = parseFloat(t.opt_ltp_entry || 0);
  const liveLtp = parseFloat(t.live_ltp || 0);
  const premiumNow = isOpen && liveLtp > 0 ? liveLtp : parseFloat(t.opt_ltp_exit || t.exit_price || 0);
  const premiumMove = premiumNow > 0 && optLtp > 0 ? premiumNow - optLtp : 0;
  const premiumMovePct = premiumNow > 0 && optLtp > 0 ? (premiumMove / optLtp) * 100 : 0;
  const cost   = optLtp > 0 ? optLtp * (t.qty || 0) : parseFloat(t.total_cost || 0);
  const exitval = isOpen ? parseFloat(t.current_value || 0) : parseFloat(t.opt_ltp_exit || 0) * (t.qty || 0);
  const opt_type = t.opt_type || (dir === "BUY" ? "CE" : "PE");
  const xprice = isOpen && liveLtp > 0 ? liveLtp : (t.opt_ltp_exit || t.exit_price || "—");

  const dirBadge = <span className={`badge ${dir === "BUY" ? "badge-buy" : "badge-sell"}`}>{opt_type === "CE" ? "CALL" : "PUT"} {dir}</span>;
  const resBadge = result === "TARGET_HIT" ? <span className="badge badge-win">WIN</span>
    : result === "SL_HIT" ? <span className="badge badge-loss">LOSS</span>
    : result === "CLOSED_EOD" ? <span className="badge badge-eod">EOD</span>
    : result === "MANUAL_CLOSE" ? <span className="badge" style={{ background: "#7c3aed22", color: "#a78bfa", border: "1px solid #7c3aed" }}>MANUAL</span>
    : <span className="badge badge-open">OPEN</span>;
  const pnlEl = pnl === 0 && !isOpen ? "—" : pnl >= 0
    ? <span className="pnl-pos">{fmt_money(pnl)}{isOpen ? " live" : ""}</span>
    : <span className="pnl-neg">{fmt_money(pnl)}{isOpen ? " live" : ""}</span>;

  return (
    <>
      <tr style={{ cursor: "pointer" }} onClick={() => setOpen(o => !o)}>
        <td>{(t.date || "").substring(0, 16)}</td>
        <td>{dirBadge}</td>
        <td style={{ color: "#8b949e", fontSize: 11 }}>{t.entry_type || ""}</td>
        <td>₹{entry.toLocaleString("en-IN")}</td>
        <td style={{ color: "#f85149" }}>₹{sl.toLocaleString("en-IN")}</td>
        <td style={{ color: "#3fb950" }}>₹{target.toLocaleString("en-IN")}</td>
        <td style={{ color: "#8b949e" }}>1:{t.rr || ""}</td>
        <td style={{ color: "#d29922" }}>{cost > 0 ? fmt_inr(cost) : "—"}</td>
        <td>
          {xprice !== "—" ? (
            <div>
              <div>₹{parseFloat(xprice).toLocaleString("en-IN")}</div>
              {isOpen && liveLtp > 0 && (
                <div style={{ fontSize: 11, color: premiumMove >= 0 ? "#3fb950" : "#f85149" }}>
                  {fmt_premium(premiumMove)} ({premiumMovePct.toFixed(2)}%)
                </div>
              )}
            </div>
          ) : "—"}
        </td>
        <td>{exitval > 0 ? fmt_inr(exitval) : "—"}</td>
        <td>{pnlEl}</td>
        <td>{resBadge}</td>
      </tr>
      {open && (
        <tr style={{ background: "#1c2128" }}>
          <td colSpan={12} style={{ padding: "10px 14px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 8, fontSize: 12 }}>
              {[
                ["Symbol",      t.option_symbol || t.symbol || "—"],
                ["Lots × Qty",  `${t.lots || "—"} × ${t.qty || "—"}`],
                ["Entry Option",  optLtp > 0 ? "₹" + optLtp.toLocaleString("en-IN") : "—", "#d29922"],
                ["Live Option",  liveLtp > 0 ? "₹" + liveLtp.toLocaleString("en-IN") : "—", isOpen ? "#58a6ff" : ""],
                ["Premium Move", premiumNow > 0 ? `${fmt_premium(premiumMove)} (${premiumMovePct.toFixed(2)}%)` : "—", premiumMove >= 0 ? "#3fb950" : "#f85149"],
                ["Live PnL",     isOpen ? fmt_money(pnl) : "—", pnl >= 0 ? "#3fb950" : "#f85149"],
                ["Current Value", exitval > 0 ? fmt_inr(exitval) : "—", isOpen ? "#58a6ff" : ""],
                ["Exit LTP",    t.opt_ltp_exit ? "₹" + parseFloat(t.opt_ltp_exit).toLocaleString("en-IN") : "—"],
                ["Nifty Entry", entry  > 0 ? "₹" + entry.toLocaleString("en-IN")  : "—"],
                ["Nifty Exit",  t.spot_exit ? "₹" + parseFloat(t.spot_exit).toLocaleString("en-IN") : "—"],
                ["Spot SL",     sl     > 0 ? "₹" + sl.toLocaleString("en-IN")     : "—", "#f85149"],
                ["Spot Target", target > 0 ? "₹" + target.toLocaleString("en-IN") : "—", "#3fb950"],
              ].map(([label, val, color]) => (
                <div key={label}>
                  <span style={{ color: "#8b949e" }}>{label}</span><br />
                  <b style={color ? { color } : {}}>{val || "—"}</b>
                </div>
              ))}
            </div>
            {isOpen && <CloseTradePanel trade={t} onClosed={onRefresh} />}
          </td>
        </tr>
      )}
    </>
  );
}

export default function TradesTable({ trades, onRefresh }) {
  const [filter, setFilter] = useState("all");
  const today = new Date().toISOString().split("T")[0];

  const filtered = filter === "today"  ? trades.filter(t => (t.date || "").includes(today))
    : filter === "wins"   ? trades.filter(t => t.status === "TARGET_HIT")
    : filter === "losses" ? trades.filter(t => t.status === "SL_HIT")
    : trades;

  return (
    <div className="table-card">
      <div className="table-header">
        <div className="table-title">Trade History</div>
        <div className="filter-tabs">
          {["all","today","wins","losses"].map(f => (
            <div key={f} className={`tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </div>
          ))}
        </div>
      </div>
      {!filtered.length ? (
        <div className="no-data">No trades yet.</div>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th>Date</th><th>Dir</th><th>Type</th><th>Entry</th><th>SL</th>
                <th>Target</th><th>RR</th><th>Cost</th><th>Exit</th><th>Exit Val</th>
                <th>PnL</th><th>Result</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, i) => <TradeRow key={i} t={t} idx={i} onRefresh={onRefresh} />)}
            </tbody>
          </table>
          <div style={{ fontSize: 11, color: "#8b949e", marginTop: 8, textAlign: "right" }}>▼ Click row for details</div>
        </>
      )}
    </div>
  );
}
