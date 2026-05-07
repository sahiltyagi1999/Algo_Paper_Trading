import { useState, useEffect } from "react";
import { api } from "../api/client";
import { useToast } from "./Toast";

function ConnDot({ ok }) {
  return <div className={`conn-dot ${ok ? "green" : "red"}`} />;
}

export default function KiteConnect() {
  const toast = useToast();
  const [status, setStatus] = useState(null);
  const [mongoOk, setMongoOk] = useState(false);
  const [loginUrl, setLoginUrl] = useState("");
  const [requestToken, setRequestToken] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [step2done, setStep2done] = useState(false);

  async function refresh() {
    try {
      const [s, m] = await Promise.all([
        api.get("/api/kite/status").catch(() => ({})),
        api.get("/api/mongo/status").catch(() => ({ connected: false })),
      ]);
      setStatus(s);
      setMongoOk(m.connected || false);
    } catch (e) {
      console.error("refresh failed:", e);
    }
  }

  useEffect(() => { refresh(); }, []);

  const envFlow = status?.has_env_creds;

  async function getLoginUrl() {
    const body = envFlow ? {} : { api_key: apiKey.trim(), api_secret: apiSecret.trim() };
    if (!envFlow && (!body.api_key || !body.api_secret)) { toast("API Key aur Secret fill karo", "error"); return; }
    const d = await api.post("/api/kite/login-url", body);
    if (d.error) { toast("Error: " + d.error, "error"); return; }
    setLoginUrl(d.login_url);
    setStep2done(true);
    window.open(d.login_url, "_blank");
    toast("Login URL ready!", "info");
  }

  async function generateToken() {
    if (!requestToken.trim()) { toast("Request token paste karo", "error"); return; }
    const body = { request_token: requestToken.trim() };
    if (!envFlow) { body.api_key = apiKey.trim(); body.api_secret = apiSecret.trim(); }
    const d = await api.post("/api/kite/generate-token", body);
    if (d.error) { toast("Error: " + d.error, "error"); return; }
    toast("Kite connected! " + (d.user || ""), "success");
    await refresh();
  }

  const connected = status?.connected;

  return (
    <div className="container" style={{ maxWidth: 700 }}>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#58a6ff", marginBottom: 4 }}>Zerodha Kite Connect</h2>
        <p style={{ fontSize: 13, color: "#8b949e" }}>Live market data aur real trading ke liye Kite se connect karo.</p>
      </div>

      <div className="conn-status" style={{ marginBottom: 12 }}>
        <ConnDot ok={mongoOk} />
        <span style={{ color: mongoOk ? "#3fb950" : "#f85149" }}>MongoDB: {mongoOk ? "Connected" : "Not connected"}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "#8b949e" }}>Token automatically save hoga</span>
      </div>

      <div className="conn-status" style={{ marginBottom: 20 }}>
        <ConnDot ok={connected} />
        <span style={{ color: connected ? "#3fb950" : "#f85149" }}>
          {connected ? `Connected — Token valid (${status?.date})` : "Not connected"}
        </span>
      </div>

      {/* ENV flow */}
      {envFlow && (
        <div className="settings-section">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <span style={{ fontSize: 18 }}>🔑</span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#3fb950" }}>API credentials detected from .env</div>
              <div style={{ fontSize: 12, color: "#8b949e", marginTop: 2 }}>API Key aur Secret already set hain — sirf login karo aur token paste karo.</div>
            </div>
          </div>

          <div className="wizard-step">
            <div className={`step-num ${connected ? "done" : ""}`}>{connected ? "✓" : "1"}</div>
            <div className="step-body">
              <h4>API Credentials — Already Set ✓</h4>
              <p>API Key aur Secret <code>.env</code> file mein hain.</p>
              <button className="btn btn-primary" onClick={getLoginUrl}>Open Zerodha Login →</button>
            </div>
          </div>

          <div className="wizard-step">
            <div className={`step-num ${step2done ? "" : "inactive"}`}>2</div>
            <div className="step-body">
              <h4>Login with Zerodha</h4>
              {loginUrl && (
                <div className="url-box"><a href={loginUrl} target="_blank" rel="noreferrer">{loginUrl}</a></div>
              )}
              <p>Login ke baad URL mein se <strong style={{ color: "#e6edf3" }}>request_token</strong> copy karo.</p>
            </div>
          </div>

          <div className="wizard-step">
            <div className={`step-num ${connected ? "done" : "inactive"}`}>{connected ? "✓" : "3"}</div>
            <div className="step-body">
              <h4>Paste Request Token &amp; Connect</h4>
              {connected ? (
                <div style={{ color: "#3fb950", fontWeight: 600, fontSize: 13 }}>
                  ✓ Kite Connected — Token valid ({status?.date})
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label className="form-label">Request Token</label>
                    <input type="text" value={requestToken} onChange={e => setRequestToken(e.target.value)} placeholder="Paste request_token value yahan" />
                  </div>
                  <button className="btn btn-success" onClick={generateToken}>✓ Connect Kite</button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Manual flow */}
      {!envFlow && status !== null && (
        <div className="settings-section">
          <div className="wizard-step">
            <div className="step-num">1</div>
            <div className="step-body">
              <h4>Enter API Credentials</h4>
              <p>Zerodha developer console → My Apps → API Key &amp; Secret copy karo.</p>
              <div className="form-grid-2">
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">API Key</label>
                  <input type="text" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="e.g. 7svg0xp2law6wcam" />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">API Secret</label>
                  <input type="password" value={apiSecret} onChange={e => setApiSecret(e.target.value)} placeholder="Your API secret" />
                </div>
              </div>
              <div style={{ marginTop: 12 }}>
                <button className="btn btn-primary" onClick={getLoginUrl}>Get Login URL →</button>
              </div>
            </div>
          </div>

          <div className="wizard-step">
            <div className={`step-num ${step2done ? "" : "inactive"}`}>2</div>
            <div className="step-body">
              <h4>Login with Zerodha</h4>
              {loginUrl && (
                <div className="url-box"><a href={loginUrl} target="_blank" rel="noreferrer">{loginUrl}</a></div>
              )}
              <p>Login ke baad URL mein se <strong style={{ color: "#e6edf3" }}>request_token</strong> copy karo.</p>
            </div>
          </div>

          <div className="wizard-step">
            <div className={`step-num ${connected ? "done" : "inactive"}`}>{connected ? "✓" : "3"}</div>
            <div className="step-body">
              <h4>Paste Request Token &amp; Connect</h4>
              {connected ? (
                <div style={{ color: "#3fb950", fontWeight: 600, fontSize: 13 }}>
                  ✓ Kite Connected — Token valid ({status?.date})
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label className="form-label">Request Token</label>
                    <input type="text" value={requestToken} onChange={e => setRequestToken(e.target.value)} placeholder="Paste request_token value yahan" />
                  </div>
                  <button className="btn btn-success" onClick={generateToken}>✓ Connect Kite</button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="settings-section" style={{ marginTop: 8 }}>
        <div className="settings-section-title">Token Info</div>
        {connected
          ? <div style={{ fontSize: 13, color: "#3fb950" }}>✓ Token valid — {status?.source === "mongodb" ? "from MongoDB" : "from file"} — Date: {status?.date}</div>
          : <div style={{ fontSize: 13, color: "#f85149" }}>✗ No valid token. Follow steps above.</div>
        }
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-ghost" onClick={refresh}>🔄 Refresh Status</button>
        </div>
      </div>

      <div className="settings-section" style={{ background: "#2d1b1b", borderColor: "#b91c1c" }}>
        <div className="settings-section-title" style={{ color: "#f85149" }}>⚠️ Important Notes</div>
        <ul style={{ fontSize: 12, color: "#8b949e", paddingLeft: 18, lineHeight: 2 }}>
          <li>Access token <strong style={{ color: "#e6edf3" }}>sirf 1 din ke liye valid</strong> — har roz repeat karo.</li>
          <li>Redirect URL Zerodha app mein <strong style={{ color: "#e6edf3" }}>http://127.0.0.1:4200</strong> set karni chahiye.</li>
          <li>API credentials <strong style={{ color: "#e6edf3" }}>kabhi bhi public share mat karo.</strong></li>
        </ul>
      </div>
    </div>
  );
}
