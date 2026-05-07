import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../api/client";

const LEVEL_COLOR = {
  ERROR:   "#f85149",
  WARNING: "#d29922",
  WARN:    "#d29922",
  INFO:    "#3fb950",
  DEBUG:   "#8b949e",
};

function colorLine(line) {
  for (const [key, color] of Object.entries(LEVEL_COLOR)) {
    if (line.includes(`[${key}]`) || line.includes(` ${key} `)) {
      return color;
    }
  }
  return "#e6edf3";
}

function LogLine({ line }) {
  const color = colorLine(line);
  // Bold the log level token
  const formatted = line.replace(
    /\[(ERROR|WARNING|WARN|INFO|DEBUG)\]/g,
    (m, lvl) => `<span style="color:${LEVEL_COLOR[lvl]};font-weight:700">${m}</span>`
  );
  return (
    <div
      style={{ color, fontFamily: "monospace", fontSize: 12, lineHeight: 1.6,
               padding: "1px 0", wordBreak: "break-all" }}
      dangerouslySetInnerHTML={{ __html: formatted }}
    />
  );
}

export default function Logs() {
  const today = new Date().toISOString().split("T")[0];
  const [date, setDate]       = useState(today);
  const [lines, setLines]     = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [filter, setFilter]   = useState("");
  const [levelFilter, setLevelFilter] = useState("ALL");
  const bottomRef = useRef(null);
  const intervalRef = useRef(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      // Fetch both MongoDB logs and live session logs in parallel
      const [dbRes, liveRes] = await Promise.all([
        api.get(`/api/logs?date=${date}&limit=500`).catch(() => ({ lines: [] })),
        api.get("/api/algo/logs").catch(() => ({ logs: [] })),
      ]);
      const dbLines   = Array.isArray(dbRes.lines) ? dbRes.lines : [];
      const liveLines = Array.isArray(liveRes.logs) ? liveRes.logs : [];
      // Merge: db lines first, then live session lines (deduplicated by content)
      const dbSet = new Set(dbLines);
      const extra = liveLines.filter(l => !dbSet.has(l));
      setLines([...dbLines, ...extra]);
    } catch (e) {
      console.error("logs fetch failed:", e);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [date]);

  useEffect(() => { load(); }, [load]);

  // Auto-scroll to bottom when lines update
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [lines, autoScroll]);

  // Auto-refresh every 5s when enabled
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => load(true), 5000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [autoRefresh, load]);

  const filtered = lines.filter(line => {
    if (levelFilter !== "ALL") {
      const lvl = levelFilter === "WARN" ? ["WARNING", "WARN"] : [levelFilter];
      if (!lvl.some(l => line.includes(`[${l}]`) || line.includes(` ${l} `))) return false;
    }
    if (filter.trim()) {
      return line.toLowerCase().includes(filter.toLowerCase());
    }
    return true;
  });

  const counts = {
    ERROR:   lines.filter(l => l.includes("[ERROR]")).length,
    WARNING: lines.filter(l => l.includes("[WARNING]") || l.includes("[WARN]")).length,
    INFO:    lines.filter(l => l.includes("[INFO]")).length,
  };

  return (
    <div className="container" style={{ maxWidth: 1100 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#58a6ff", marginBottom: 4 }}>Algo Logs</h2>
          <p style={{ fontSize: 13, color: "#8b949e" }}>MongoDB se live backend logs — real-time trading activity.</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3",
                     borderRadius: 4, padding: "5px 8px", fontSize: 12 }}
          />
          <button className="btn btn-ghost" onClick={() => load()} style={{ fontSize: 12 }}>
            🔄 Refresh
          </button>
          <button
            onClick={() => setAutoRefresh(a => !a)}
            style={{
              background: autoRefresh ? "#0e4429" : "#21262d",
              border: `1px solid ${autoRefresh ? "#3fb950" : "#30363d"}`,
              color: autoRefresh ? "#3fb950" : "#8b949e",
              borderRadius: 4, padding: "5px 12px", fontSize: 12, cursor: "pointer",
            }}
          >
            {autoRefresh ? "⏸ Auto ON" : "▶ Auto OFF"}
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
        {[
          ["ALL",     `All (${lines.length})`,     "#8b949e"],
          ["INFO",    `✓ INFO (${counts.INFO})`,    "#3fb950"],
          ["WARN",    `⚠ WARN (${counts.WARNING})`, "#d29922"],
          ["ERROR",   `✕ ERROR (${counts.ERROR})`,  "#f85149"],
        ].map(([val, label, color]) => (
          <button
            key={val}
            onClick={() => setLevelFilter(val)}
            style={{
              background: levelFilter === val ? color + "22" : "#21262d",
              border: `1px solid ${levelFilter === val ? color : "#30363d"}`,
              color: levelFilter === val ? color : "#8b949e",
              borderRadius: 4, padding: "4px 12px", fontSize: 12, cursor: "pointer",
            }}
          >
            {label}
          </button>
        ))}

        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Search logs…"
          style={{ background: "#0d1117", border: "1px solid #30363d", color: "#e6edf3",
                   borderRadius: 4, padding: "4px 10px", fontSize: 12, flex: 1, minWidth: 180 }}
        />

        <button
          onClick={() => setAutoScroll(a => !a)}
          style={{
            background: "#21262d", border: "1px solid #30363d",
            color: autoScroll ? "#58a6ff" : "#8b949e",
            borderRadius: 4, padding: "4px 12px", fontSize: 12, cursor: "pointer",
          }}
          title="Auto-scroll to latest"
        >
          {autoScroll ? "⬇ Scroll: ON" : "⬇ Scroll: OFF"}
        </button>
      </div>

      {/* Log window */}
      <div
        style={{
          background: "#0d1117", border: "1px solid #30363d", borderRadius: 6,
          height: 520, overflowY: "auto", padding: "12px 16px",
          fontFamily: "monospace",
        }}
      >
        {loading && <div style={{ color: "#8b949e", fontSize: 12 }}>Loading…</div>}
        {!loading && filtered.length === 0 && (
          <div style={{ color: "#8b949e", fontSize: 12, textAlign: "center", marginTop: 60 }}>
            {lines.length === 0
              ? `No logs found for ${date}. Algo is not running or no data in MongoDB.`
              : "No lines match the current filter."}
          </div>
        )}
        {filtered.map((line, i) => <LogLine key={i} line={line} />)}
        <div ref={bottomRef} />
      </div>

      <div style={{ fontSize: 11, color: "#6e7681", marginTop: 8, display: "flex", justifyContent: "space-between" }}>
        <span>Showing {filtered.length} of {lines.length} lines{filter ? ` matching "${filter}"` : ""}</span>
        {autoRefresh && <span style={{ color: "#3fb950" }}>● Auto-refreshing every 5s</span>}
      </div>
    </div>
  );
}
