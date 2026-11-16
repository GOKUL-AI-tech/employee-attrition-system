import { useEffect, useState } from "react";
import { api } from "../api";
import { PageHead, Panel, RiskBadge, RISK_COLORS } from "../components/ui.jsx";
import { EmployeeFields } from "./Employees.jsx";

const DEFAULT = { age: 30, gender: "Male", department: "", job_role: "", monthly_income: 5000, years_at_company: 3,
  job_satisfaction: 3, work_life_balance: 3, overtime: "No", job_level: 2, performance_rating: 3,
  distance_from_home: 10, num_companies_worked: 1, training_times_last_year: 2 };

export default function Predict() {
  const [f, setF] = useState(DEFAULT);
  const [meta, setMeta] = useState({ departments: [], roles: {} });
  const [res, setRes] = useState(null);
  const [hist, setHist] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const loadHist = () => api.get("/predict/history").then(setHist).catch(() => {});
  useEffect(() => { api.get("/employees/meta").then(setMeta); loadHist(); }, []);

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setBusy(true);
    try { setRes(await api.post("/predict", f)); loadHist(); } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  const maxImpact = res ? Math.max(...res.factors.map((x) => Math.abs(x.impact)), 1) : 1;

  return (
    <>
      <PageHead title="Attrition Prediction" sub="Enter employee details to estimate the likelihood of leaving" />
      <div className="grid predict">
        <Panel title="Employee Details">
          <form onSubmit={submit}>
            {err && <div className="alert">{err}</div>}
            <EmployeeFields f={f} set={setF} meta={meta} showIdentity={false} showAttrition={false} />
            <button className="btn primary block mt" disabled={busy}>{busy ? "Predicting…" : "Predict Attrition"}</button>
          </form>
        </Panel>
        <div>
          <Panel title="Prediction Result">
            {!res ? <p className="muted">Submit the form to see the prediction.</p> : (
              <>
                <div className="result">
                  <div className="gauge" style={{ "--p": res.probability, "--c": RISK_COLORS[res.risk_level] }}><span>{res.probability}%</span></div>
                  <div>
                    <div className="muted small">Prediction</div>
                    <div className={"verdict " + res.risk_level.toLowerCase()}>{res.prediction}</div>
                    <div className="mt-s">Risk level: <RiskBadge level={res.risk_level} /></div>
                  </div>
                </div>
                <h4>Main factors affecting this prediction</h4>
                {res.factors.length ? res.factors.map((x) => (
                  <div className="factor" key={x.feature}>
                    <div className="factor-top"><span>{x.feature}: <b>{String(x.value)}</b></span>
                      <span className={x.impact > 0 ? "up" : "down"}>{x.impact > 0 ? "▲" : "▼"} {Math.abs(x.impact)} pts · {x.direction}</span></div>
                    <div className="bar"><div style={{ width: (Math.abs(x.impact) / maxImpact) * 100 + "%", background: x.impact > 0 ? "#e5484d" : "#22a06b" }} /></div>
                  </div>)) : <p className="muted">No single factor stands out.</p>}
                <p className="muted small">Impact = change in leave probability versus a typical employee for that attribute.</p>
              </>)}
          </Panel>
          <Panel title="Recent Predictions">
            <table><thead><tr><th>Department</th><th>Role</th><th>Prob.</th><th>Risk</th></tr></thead>
              <tbody>{hist.slice(0, 6).map((h) => <tr key={h.id}><td>{h.department}</td><td>{h.job_role}</td><td>{h.probability}%</td><td><RiskBadge level={h.risk_level} /></td></tr>)}
                {!hist.length && <tr><td colSpan="4" className="muted center">None yet</td></tr>}</tbody></table>
          </Panel>
        </div>
      </div>
    </>
  );
}
