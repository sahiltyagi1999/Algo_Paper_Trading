import { useState, useCallback, useEffect } from "react";
import { ToastProvider } from "./components/Toast";
import Header from "./components/Header";
import NavTabs from "./components/NavTabs";
import Dashboard from "./components/Dashboard";
import KiteConnect from "./components/KiteConnect";
import Settings from "./components/Settings";
import Docs from "./components/Docs";
import GoLive from "./components/GoLive";
import AuthPage from "./components/AuthPage";
import { api, clearToken } from "./api/client";
import { useInterval } from "./hooks/useInterval";

function App() {
  const [authed, setAuthed]         = useState(!!localStorage.getItem("jwt_token"));
  const [username, setUsername]     = useState(localStorage.getItem("username") || "");
  const [tab, setTab]               = useState("dashboard");
  const [lastUpdated, setLastUpdated] = useState("");
  const [running, setRunning]       = useState(false);

  const [summary, setSummary]     = useState(null);
  const [equity, setEquity]       = useState([]);
  const [todayEquity, setTodayEq] = useState([]);
  const [candles, setCandles]     = useState([]);
  const [vix, setVix]             = useState(null);
  const [oi, setOi]               = useState({});
  const [trades, setTrades]       = useState([]);
  const [settings, setSettings]   = useState(null);

  // Handle token expiry from anywhere
  useEffect(() => {
    const handler = () => { setAuthed(false); setUsername(""); };
    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, []);

  function handleAuth(user) {
    localStorage.setItem("username", user);
    setUsername(user);
    setAuthed(true);
  }

  function handleLogout() {
    clearToken();
    localStorage.removeItem("username");
    setAuthed(false);
    setUsername("");
  }

  const loadAll = useCallback(async () => {
    if (!authed) return;
    try {
      const [sum, eq, teq, v, o, tr, st, status] = await Promise.all([
        api.get("/api/summary"),
        api.get("/api/equity"),
        api.get("/api/todays_equity"),
        api.get("/api/vix"),
        api.get("/api/oi"),
        api.get("/api/trades"),
        api.get("/api/settings"),
        api.get("/api/status"),
      ]);
      setSummary(sum);
      setEquity(eq);
      setTodayEq(teq);
      setVix(v);
      setOi(o);
      setTrades(tr);
      setSettings(st);
      setRunning(status?.running || false);
      setLastUpdated("Last updated: " + new Date().toLocaleTimeString("en-IN"));
      api.get("/api/candles").then(c => { if (c?.length) setCandles(c); }).catch(() => {});
    } catch (e) {
      console.error("loadAll:", e);
    }
  }, [authed]);

  useEffect(() => { if (authed) loadAll(); }, [authed, loadAll]);
  useInterval(loadAll, authed ? 30000 : null);

  if (!authed) return <ToastProvider><AuthPage onAuth={handleAuth} /></ToastProvider>;

  return (
    <ToastProvider>
      <Header
        running={running} lastUpdated={lastUpdated} onRefresh={loadAll}
        username={username} onLogout={handleLogout}
      />
      <NavTabs active={tab} onSelect={t => { setTab(t); if (t === "dashboard") loadAll(); }} />
      {tab === "dashboard" && (
        <Dashboard
          summary={summary} equity={equity} todayEquity={todayEquity}
          candles={candles} vix={vix} oi={oi} trades={trades} settings={settings}
          onRefresh={loadAll}
        />
      )}
      {tab === "kite"     && <KiteConnect />}
      {tab === "settings" && <Settings />}
      {tab === "docs"     && <Docs />}
      {tab === "golive"   && <GoLive />}
    </ToastProvider>
  );
}

export default App;
