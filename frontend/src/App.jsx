import { useState, useCallback, useEffect } from "react";
import { ToastProvider } from "./components/Toast";
import Header from "./components/Header";
import NavTabs from "./components/NavTabs";
import Dashboard from "./components/Dashboard";
import KiteConnect from "./components/KiteConnect";
import Settings from "./components/Settings";
import Docs from "./components/Docs";
import GoLive from "./components/GoLive";
import Logs from "./components/Logs";
import AuthPage from "./components/AuthPage";
import { api, clearToken } from "./api/client";
import { useInterval } from "./hooks/useInterval";

function App() {
  const [authed, setAuthed]         = useState(!!localStorage.getItem("jwt_token"));
  const [username, setUsername]     = useState(localStorage.getItem("username") || "");
  const [tab, setTab]               = useState("dashboard");
  const [lastUpdated, setLastUpdated] = useState("");
  const [running, setRunning]       = useState(false);
  const [algoStatus, setAlgoStatus] = useState(null);

  const [sessionExpired, setSessionExpired] = useState(false);

  const [summary, setSummary]     = useState(null);
  const [equity, setEquity]       = useState([]);
  const [todayEquity, setTodayEq] = useState([]);
  const [candles, setCandles]     = useState([]);
  const [vix, setVix]             = useState(null);
  const [oi, setOi]               = useState({});
  const [trades, setTrades]       = useState([]);
  const [settings, setSettings]   = useState(null);
  const hasOpenTrades = trades.some(t => t?.status === "OPEN");

  // Handle token expiry from anywhere (401 response)
  useEffect(() => {
    const handler = () => {
      setAuthed(false);
      setUsername("");
      setSessionExpired(true);
    };
    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, []);


  function handleAuth(user, password) {
    localStorage.setItem("username", user);
    if (password) localStorage.setItem("_pwd", password);
    setUsername(user);
    setAuthed(true);
    setSessionExpired(false);
  }

  function handleLogout() {
    clearToken();
    localStorage.removeItem("username");
    localStorage.removeItem("_pwd");
    setAuthed(false);
    setUsername("");
    setSessionExpired(false);
  }

  const loadAll = useCallback(async () => {
    if (!authed) return;

    // Fast: critical data first — renders immediately
    api.get("/api/summary").then(d => { if (d && !d.error) setSummary(d); }).catch(() => {});
    api.get("/api/trades").then(d => { if (Array.isArray(d)) setTrades(d); }).catch(() => {});
    api.get("/api/algo/status").then(d => {
      setAlgoStatus(d || null);
      setRunning(d?.running || false);
    }).catch(() => {});

    // Medium: charts
    api.get("/api/equity").then(d => { if (Array.isArray(d)) setEquity(d); }).catch(() => {});
    api.get("/api/todays_equity").then(d => { if (Array.isArray(d)) setTodayEq(d); }).catch(() => {});
    api.get("/api/settings").then(d => { if (d && !d.error) setSettings(d); }).catch(() => {});

    // Slow: market data (VIX hits NSE, OI hits Kite) — non-blocking
    api.get("/api/vix").then(d => { if (d) setVix(d); }).catch(() => {});
    api.get("/api/oi").then(d => { if (d) setOi(d); }).catch(() => {});
    api.get("/api/candles").then(d => { if (Array.isArray(d) && d.length) setCandles(d); }).catch(() => {});

    setLastUpdated("Last updated: " + new Date().toLocaleTimeString("en-IN"));
  }, [authed]);

  // After start/stop, poll status rapidly for 5s to catch the change fast
  const pollStatus = useCallback(() => {
    let attempts = 0;
    const id = setInterval(async () => {
      attempts++;
      try {
        const d = await api.get("/api/algo/status");
        setAlgoStatus(d || null);
        setRunning(d?.running || false);
      } catch { /* ignore */ }
      if (attempts >= 5) clearInterval(id);
    }, 1000);
  }, []);

  useEffect(() => { if (authed) loadAll(); }, [authed, loadAll]);
  useInterval(loadAll, authed ? (running || hasOpenTrades ? 5000 : 30000) : null);

  if (!authed) return <ToastProvider><AuthPage onAuth={handleAuth} sessionExpired={sessionExpired} /></ToastProvider>;

  return (
    <ToastProvider>
      <Header
        running={running} lastUpdated={lastUpdated} onRefresh={loadAll}
        username={username} onLogout={handleLogout} settings={settings}
        onPollStatus={pollStatus} algoStatus={algoStatus}
      />
      <NavTabs active={tab} onSelect={t => { setTab(t); if (t === "dashboard") loadAll(); }} />
      {tab === "dashboard" && (
        <Dashboard
          summary={summary} equity={equity} todayEquity={todayEquity}
          candles={candles} vix={vix} oi={oi} trades={trades} settings={settings}
          algoStatus={algoStatus}
          onRefresh={loadAll}
        />
      )}
      {tab === "kite"     && <KiteConnect />}
      {tab === "settings" && <Settings />}
      {tab === "logs"     && <Logs />}
      {tab === "docs"     && <Docs />}
      {tab === "golive"   && <GoLive />}
    </ToastProvider>
  );
}

export default App;
