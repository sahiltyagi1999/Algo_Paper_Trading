import { useState } from "react";
import { api, setToken } from "../api/client";

export default function AuthPage({ onAuth }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const d = await api.post("/api/auth/login", { username, password });
      if (d.error) { setError(d.error); return; }
      setToken(d.token);
      onAuth(d.username || username);
    } catch {
      setError("Connection failed — is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#0d1117",
    }}>
      <div style={{
        background: "#161b22", border: "1px solid #30363d", borderRadius: 12,
        padding: "40px 36px", width: "100%", maxWidth: 380,
      }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#58a6ff" }}>
            8-30 EMA <span style={{ color: "#3fb950" }}>Algo</span>
          </div>
          <div style={{ fontSize: 13, color: "#8b949e", marginTop: 6 }}>Dashboard</div>
        </div>

        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text" value={username} autoComplete="username"
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username" required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password" value={password} autoComplete="current-password"
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password" required
            />
          </div>

          {error && (
            <div style={{ background: "#2d1b1b", border: "1px solid #b91c1c", borderRadius: 6, padding: "10px 12px", fontSize: 12, color: "#f85149", marginBottom: 16 }}>
              {error}
            </div>
          )}

          <button
            type="submit" className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center", padding: "10px 0", fontSize: 14 }}
            disabled={loading}
          >
            {loading ? "Please wait..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
