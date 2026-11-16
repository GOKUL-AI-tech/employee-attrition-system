import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Login() {
  const [f, setF] = useState({ username: "", password: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();
  const submit = async (e) => {
    e.preventDefault(); setErr(""); setBusy(true);
    try { const r = await api.post("/auth/login", f); setToken(r.token); nav("/"); }
    catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <div className="brand"><span className="logo">A</span> AttritionIQ</div>
        <h2>HR Admin Login</h2>
        <p className="muted">Sign in to view attrition insights.</p>
        {err && <div className="alert">{err}</div>}
        <label>Username<input value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} autoFocus required /></label>
        <label>Password<input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required /></label>
        <button className="btn primary block" disabled={busy}>{busy ? "Signing in…" : "Login"}</button>
        <p className="hint">Demo: admin / admin123</p>
      </form>
    </div>
  );
}
