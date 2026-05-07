const BASE = import.meta.env.VITE_API_BASE || "http://localhost:4200";

function getToken() {
  return localStorage.getItem("jwt_token") || "";
}

export function setToken(t) {
  localStorage.setItem("jwt_token", t);
  // Store expiry as ms timestamp (decode exp from JWT payload)
  try {
    const payload = JSON.parse(atob(t.split(".")[1]));
    if (payload.exp) localStorage.setItem("jwt_exp", payload.exp * 1000);
  } catch { /* ignore */ }
}

export function clearToken() {
  localStorage.removeItem("jwt_token");
  localStorage.removeItem("jwt_exp");
}

export function getTokenExpiry() {
  const exp = localStorage.getItem("jwt_exp");
  return exp ? parseInt(exp, 10) : null;
}

async function req(path, opts = {}) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  });
  if (res.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("auth:logout"));
  }
  try {
    return await res.json();
  } catch {
    return { error: `Server error ${res.status}` };
  }
}

export const api = {
  get:  (path)       => req(path),
  post: (path, body) => req(path, { method: "POST", body: JSON.stringify(body) }),
};
