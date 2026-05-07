const TABS = [
  { id: "dashboard", label: "📊 Dashboard" },
  { id: "kite",      label: "🔌 Kite Connect" },
  { id: "settings",  label: "⚙️ Settings" },
  { id: "logs",      label: "🖥 Logs" },
  { id: "docs",      label: "📚 Documentation" },
  { id: "golive",    label: "🚀 Go Live" },
];

export default function NavTabs({ active, onSelect }) {
  return (
    <div style={{
      background: "#161b22", borderBottom: "1px solid #30363d",
      display: "flex", padding: "0 24px", gap: 4,
    }}>
      {TABS.map(t => (
        <div
          key={t.id}
          onClick={() => onSelect(t.id)}
          style={{
            padding: "10px 16px", fontSize: 13, fontWeight: 500,
            color: active === t.id ? "#58a6ff" : "#8b949e",
            cursor: "pointer",
            borderBottom: `2px solid ${active === t.id ? "#58a6ff" : "transparent"}`,
            transition: "color .2s, border-color .2s",
          }}
        >
          {t.label}
        </div>
      ))}
    </div>
  );
}
