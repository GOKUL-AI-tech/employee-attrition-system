import { useEffect, useState } from "react";
import { api } from "../api";
import { PageHead, Panel, RiskBadge } from "../components/ui.jsx";

export default function Risk() {
  const [rows, setRows] = useState([]);
  const [level, setLevel] = useState("");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [factors, setFactors] = useState([]);
  useEffect(() => { api.get("/risk?level=" + level).then(setRows); }, [level]);
  const shown = rows.filter((r) => (r.name + r.employee_id + r.department).toLowerCase().includes(q.toLowerCase()));

  const open = async (r) => { setSel(r); setFactors([]); setFactors(await api.get(`/employees/${r.id}/factors`)); };

  return (
    <>
      <PageHead title="Employee Risk Analysis" sub="Employees ranked by predicted attrition probability">
        <button className="btn" onClick={() => api.download("/reports/export?type=risk", "risk_export.csv")}>Export CSV</button>
      </PageHead>
      <Panel title="Risk Table">
        <div className="toolbar">
          <input placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">All risk levels</option><option>High</option><option>Medium</option><option>Low</option>
          </select>
        </div>
        <div className="table-wrap tall"><table>
          <thead><tr><th>Employee ID</th><th>Name</th><th>Department</th><th>Job Role</th><th>Probability</th><th>Risk</th><th>Prediction</th></tr></thead>
          <tbody>{shown.slice(0, 300).map((r) => (
            <tr key={r.id} className={"clickable " + (r.risk_level === "High" ? "row-high" : "")} onClick={() => open(r)}>
              <td>{r.employee_id}</td><td>{r.name}</td><td>{r.department}</td><td>{r.job_role}</td>
              <td><div className="probcell"><b>{r.probability}%</b><div className="bar"><div style={{ width: r.probability + "%", background: r.risk_level === "High" ? "#e5484d" : r.risk_level === "Medium" ? "#f0a020" : "#22a06b" }} /></div></div></td>
              <td><RiskBadge level={r.risk_level} /></td><td>{r.prediction}</td></tr>))}
            {!shown.length && <tr><td colSpan="7" className="muted center">No results</td></tr>}</tbody>
        </table></div>
        <p className="muted small">Click a row to see the main risk drivers. Showing up to 300 rows.</p>
      </Panel>
      {sel && (
        <div className="modal-bg" onMouseDown={(e) => e.target === e.currentTarget && setSel(null)}>
          <div className="modal narrow">
            <h2>{sel.name} <RiskBadge level={sel.risk_level} /></h2>
            <p className="muted">{sel.job_role} · {sel.department} · {sel.probability}% likelihood of leaving</p>
            <h4>Main factors</h4>
            {factors.length ? factors.map((x) => (
              <div className="factor-top pad" key={x.feature}><span>{x.feature}: <b>{String(x.value)}</b></span>
                <span className={x.impact > 0 ? "up" : "down"}>{x.impact > 0 ? "▲" : "▼"} {Math.abs(x.impact)} pts</span></div>)) : <p className="muted">Loading…</p>}
            <div className="modal-actions"><button className="btn" onClick={() => setSel(null)}>Close</button></div>
          </div>
        </div>)}
    </>
  );
}
