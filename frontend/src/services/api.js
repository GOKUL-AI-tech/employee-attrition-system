// All backend calls live here. Errors are turned into friendly messages.
const TOKEN_KEY = "attrition_token";

export const auth = {
  get token() {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set(token) {
    try { localStorage.setItem(TOKEN_KEY, token); } catch { /* ignore */ }
  },
  clear() {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  },
};

export class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.status = status;
    this.fields = fields || {};
  }
}

async function request(path, { method = "GET", body, params } = {}) {
  let url = `/api${path}`;
  if (params) {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null));
    if (qs.toString()) url += `?${qs}`;
  }

  let res;
  try {
    res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Please make sure the backend is running.", 0);
  }

  let data = null;
  try { data = await res.json(); } catch { /* non-JSON response */ }

  if (!res.ok) {
    if (res.status === 401 && path !== "/login") {
      auth.clear();
      window.dispatchEvent(new Event("auth-expired"));
    }
    throw new ApiError(data?.error || "Something went wrong. Please try again.", res.status, data?.fields);
  }
  return data;
}

export const api = {
  login: (username, password) => request("/login", { method: "POST", body: { username, password } }),
  logout: () => request("/logout", { method: "POST" }).catch(() => null),
  options: () => request("/options"),
  employees: (params) => request("/employees", { params }),
  employee: (id) => request(`/employees/${id}`),
  createEmployee: (body) => request("/employees", { method: "POST", body }),
  updateEmployee: (id, body) => request(`/employees/${id}`, { method: "PUT", body }),
  deleteEmployee: (id) => request(`/employees/${id}`, { method: "DELETE" }),
  predict: (body) => request("/predict", { method: "POST", body }),
  predictions: () => request("/predictions"),
  dashboard: () => request("/dashboard"),
  metrics: () => request("/model-metrics"),
  settings: () => request("/settings"),
  retrain: () => request("/retrain", { method: "POST" }),
};
