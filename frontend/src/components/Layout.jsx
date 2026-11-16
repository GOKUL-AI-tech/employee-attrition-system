import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { setToken } from "../api";

const links = [
  ["/", "Dashboard", "▦"], ["/employees", "Employees", "☰"], ["/predict", "Predict Attrition", "✦"],
  ["/risk", "Risk Analysis", "⚠"], ["/analytics", "HR Analytics", "▤"], ["/reports", "Reports", "⎙"],
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  return (
    <div className="shell">
      <aside className={"sidebar" + (open ? " open" : "")}>
        <div className="brand"><span className="logo">A</span> AttritionIQ</div>
        <nav>
          {links.map(([to, label, icon]) => (
            <NavLink key={to} to={to} end={to === "/"} onClick={() => setOpen(false)}
              className={({ isActive }) => "navlink" + (isActive ? " active" : "")}>
              <span className="ico">{icon}</span>{label}
            </NavLink>
          ))}
        </nav>
        <button className="navlink logout" onClick={() => { setToken(null); nav("/login"); }}>
          <span className="ico">⏻</span>Sign out
        </button>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setOpen(!open)}>☰</button>
          <span className="topbar-title">HR Attrition Prediction &amp; Analytics</span>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  );
}
