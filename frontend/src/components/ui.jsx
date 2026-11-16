export const Card = ({ label, value, sub, tone }) => (
  <div className={"stat " + (tone || "")}>
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
    {sub && <div className="stat-sub">{sub}</div>}
  </div>
);

export const Panel = ({ title, children, action }) => (
  <section className="panel">
    <div className="panel-head"><h3>{title}</h3>{action}</div>
    {children}
  </section>
);

export const RiskBadge = ({ level }) => <span className={"badge " + (level || "").toLowerCase()}>{level}</span>;

export const PageHead = ({ title, sub, children }) => (
  <div className="page-head">
    <div><h1>{title}</h1>{sub && <p className="muted">{sub}</p>}</div>
    <div className="actions">{children}</div>
  </div>
);

export const COLORS = { blue: "#4f6ef7", teal: "#14b8a6", low: "#22a06b", medium: "#f0a020", high: "#e5484d", grid: "#e6e9f0" };
export const RISK_COLORS = { Low: COLORS.low, Medium: COLORS.medium, High: COLORS.high };
export const money = (n) => "$" + Math.round(n).toLocaleString();
