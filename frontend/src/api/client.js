const BASE = import.meta.env.VITE_API_BASE || "http://localhost:4200";

function getToken() {
  return localStorage.getItem("jwt_token") || "";
}

export function setToken(t) {
  localStorage.setItem("jwt_token", t);
}

export function clearToken() {
  localStorage.removeItem("jwt_token");
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
  return res.json();
}

export const api = {
  get:  (path)       => req(path),
  post: (path, body) => req(path, { method: "POST", body: JSON.stringify(body) }),
};
