export default function Header({ running, lastUpdated, onRefresh, username, onLogout }) {
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
      </div>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <span
          style={{
            padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 600,
            background: running ? "#0d4429" : "#2d1b1b",
            border: `1px solid ${running ? "#3fb950" : "#f85149"}`,
            color: running ? "#3fb950" : "#f85149",
          }}
        >
          ● {running ? "Algo Running" : "Algo Stopped"}
        </span>
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
