const KEY = "attrition_token";
export const getToken = () => localStorage.getItem(KEY);
export const setToken = (t) => (t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY));

async function req(path, opts = {}) {
  const res = await fetch("/api" + path, {
    ...opts,
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + (getToken() || ""), ...(opts.headers || {}) },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (res.status === 401 && !path.startsWith("/auth/login")) {
    setToken(null);
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

export const api = {
  get: (p) => req(p),
  post: (p, body) => req(p, { method: "POST", body }),
  put: (p, body) => req(p, { method: "PUT", body }),
  del: (p) => req(p, { method: "DELETE" }),
  async download(path, filename) {
    const res = await fetch("/api" + path, { headers: { Authorization: "Bearer " + getToken() } });
    if (!res.ok) throw new Error("Download failed");
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    a.click();
    URL.revokeObjectURL(url);
  },
};
