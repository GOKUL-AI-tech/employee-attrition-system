import { useEffect, useState } from "react";
import { api } from "../api";
import { Card, money, PageHead, Panel } from "../components/ui.jsx";

export default function Reports() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api.get("/reports/summary").then(setS);
  useEffect(() => { load(); }, []);
  const dl = (type) => api.download(`/reports/export?type=${type}`, `${type}_export.csv`);
  const retrain = async () => {
    setBusy(true); setMsg("");
    try { const r = await api.post("/model/retrain"); setMsg(`Model retrained · accuracy ${r.metrics.accuracy}, ROC-AUC ${r.metrics.roc_auc}`); load(); }
    catch (e) { setMsg(e.message); } finally { setBusy(false); }
  };
  if (!s) return <p className="muted">Loading…</p>;
  return (
    <>
      <PageHead title="Reports" sub="Summary statistics and data export">
        <button className="btn" onClick={() => dl("employees")}>Export Employees CSV</button>
        <button className="btn primary" onClick={() => dl("risk")}>Export Risk CSV</button>
      </PageHead>
      <div className="grid cards">
        <Card label="Total Employees" value={s.total} />
        <Card label="Predicted Attrition" value={s.predicted_attrition} sub={`${s.predicted_attrition_pct}% of workforce`} tone="danger" />
        <Card label="High-Risk Employees" value={s.high_risk_count} tone="danger" />
        <Card label="Overall Attrition" value={s.attrition_pct + "%"} sub={`${s.actual_attrition} employees left`} />
      </div>
      <Panel title="Department-wise Statistics">
        <div className="table-wrap"><table>
          <thead><tr><th>Department</th><th>Employees</th><th>Left</th><th>Attrition %</th><th>High Risk</th><th>Avg Salary</th><th>Avg Satisfaction</th></tr></thead>
          <tbody>{s.departments.map((d) => <tr key={d.department}><td>{d.department}</td><td>{d.total}</td><td>{d.left}</td><td>{d.rate}%</td><td>{d.high_risk}</td><td>{money(d.avg_salary)}</td><td>{d.avg_satisfaction}</td></tr>)}</tbody>
        </table></div>
      </Panel>
      <Panel title={`High-Risk Employees (top ${s.high_risk.length})`}>
        <div className="table-wrap tall"><table>
          <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Role</th><th>Probability</th></tr></thead>
          <tbody>{s.high_risk.map((e) => <tr key={e.employee_id} className="row-high"><td>{e.employee_id}</td><td>{e.name}</td><td>{e.department}</td><td>{e.job_role}</td><td><b>{e.probability}%</b></td></tr>)}</tbody>
        </table></div>
      </Panel>
      <Panel title="Prediction Model" action={<button className="btn sm" onClick={retrain} disabled={busy}>{busy ? "Training…" : "Retrain model"}</button>}>
        <p className="muted">Retrain the Random Forest on the current employee records in the database (run after adding many employees or changing attrition outcomes).</p>
        {msg && <div className="alert info">{msg}</div>}
      </Panel>
    </>
  );
}
