import { useState } from "react";
import { api } from "../api/client";

export default function Header({ running, lastUpdated, onRefresh, username, onLogout, settings, onPollStatus, algoStatus }) {
  const [acting, setActing] = useState(false);
  const lastClosed = algoStatus?.last_data_status?.latest_closed_candle || algoStatus?.last_closed_candle;
  const lastReason = algoStatus?.last_signal_diag?.reason;

  async function toggleAlgo() {
    setActing(true);
    try {
      if (running) {
        await api.post("/api/algo/stop", {});
      } else {
        const body = settings ? {
          instrument:       settings.instrument,
          paper_trading:    settings.paper_trading,
          capital:          settings.capital,
          daily_loss_limit: settings.daily_loss_limit,
          max_trades_day:   settings.max_trades_day,
          risk_pct:         settings.risk_pct,
          ema_fast:         settings.ema_fast,
          ema_slow:         settings.ema_slow,
        } : {};
        await api.post("/api/algo/start", body);
      }
      // Poll status every 1s for 5s so badge updates instantly
      onPollStatus();
    } catch (e) {
      console.error("toggleAlgo:", e);
    } finally {
      setActing(false);
    }
  }

  return (
    <header style={{
      background: "#161b22", borderBottom: "1px solid #30363d",
      padding: "14px 24px", display: "flex", alignItems: "center",
      justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100,
    }}>
      <div>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: "#58a6ff" }}>
          8-30 EMA <span style={{ color: "#3fb950" }}>Algo</span> Dashboard
        </h1>
        <div style={{ fontSize: 11, color: "#8b949e" }}>{lastUpdated || "Loading..."}</div>
        {algoStatus?.running && (
          <div style={{ fontSize: 11, color: "#6e7681", marginTop: 3 }}>
            Closed candle: {lastClosed || "waiting"}{lastReason ? ` | ${lastReason}` : ""}
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>

        {/* Status badge */}
        <span style={{
          padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600,
          background: running ? "#0d4429" : "#2d1b1b",
          border: `1px solid ${running ? "#3fb950" : "#f85149"}`,
          color: running ? "#3fb950" : "#f85149",
        }}>
          ● {running ? "Algo Running" : "Algo Stopped"}
        </span>

        {/* Start / Stop button */}
        <button
          onClick={toggleAlgo}
          disabled={acting}
          style={{
            padding: "5px 14px", borderRadius: 6, fontSize: 12, fontWeight: 700,
            cursor: acting ? "not-allowed" : "pointer", border: "none",
            background: acting ? "#333" : running ? "#b91c1c" : "#166534",
            color: "#fff",
          }}
        >
          {acting ? "..." : running ? "⏹ Stop Algo" : "▶ Start Algo"}
        </button>

        <button className="btn btn-primary btn-sm" onClick={onRefresh}>Refresh</button>

        {username && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "#8b949e" }}>👤 {username}</span>
            <button
              className="btn btn-ghost btn-sm"
              onClick={onLogout}
              style={{ fontSize: 11, padding: "4px 10px" }}
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
