import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Info } from "lucide-react";
import { Alert, Loading, PageHeader, RiskBadge, RISK_COLORS, formatDate, money, useLoad } from "../components/ui.jsx";
import { api } from "../services/api.js";

const stars = (n, max = 4) => `${n} / ${max}`;

export function FactorList({ risk = [], protective = [] }) {
  return (
    <>
      {risk.length === 0 && <p className="muted">No factors stood out as increasing the predicted risk.</p>}
      <ul className="factor-list">
        {risk.map((f) => (
          <li key={f.feature} className="factor up">
            <span className="factor-dot" />
            <span>{f.text}</span>
          </li>
        ))}
        {protective.map((f) => (
          <li key={f.feature} className="factor down">
            <span className="factor-dot" />
            <span>{f.text}</span>
          </li>
        ))}
      </ul>
      <p className="muted small disclaimer"><Info size={14} /> These factors describe patterns the model associates with attrition. They are not proof that this employee will leave.</p>
    </>
  );
}

export default function EmployeeDetail() {
  const { id } = useParams();
  const { data: e, error, loading } = useLoad(() => api.employee(id), [id]);

  if (loading) return <Loading />;
  if (error) return (<><Link to="/employees" className="back-link"><ArrowLeft size={16} /> Back</Link><Alert>{error}</Alert></>);

  const profile = [
    ["Name", e.name], ["Employee ID", e.employee_id], ["Age", e.age], ["Gender", e.gender],
    ["Department", e.department], ["Job Role", e.job_role], ["Job Level", e.job_level],
    ["Monthly Income", money(e.monthly_income)], ["Years at Company", e.years_at_company],
    ["Total Working Years", e.total_working_years], ["Job Satisfaction", stars(e.job_satisfaction)],
    ["Work-Life Balance", stars(e.work_life_balance)], ["Overtime", e.overtime],
    ["Distance From Home", `${e.distance_from_home} km`], ["Performance Rating", stars(e.performance_rating)],
    ["Companies Worked", e.num_companies_worked], ["Training Last Year", `${e.training_times}x`],
    ["Marital Status", e.marital_status], ["Business Travel", e.business_travel.replace(/_/g, " ")],
  ];

  return (
    <>
      <Link to="/employees" className="back-link"><ArrowLeft size={16} /> Back to employees</Link>
      <PageHeader title={e.name} subtitle={`${e.employee_id} · ${e.job_role} · ${e.department}`} />

      <div className="detail-grid">
        <div className="card">
          <h3>Employee Profile</h3>
          <dl className="profile-grid">
            {profile.map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{v}</dd></div>))}
          </dl>
        </div>

        <div className="stack">
          <div className="card">
            <h3>AI Result</h3>
            <div className="result-row">
              <div>
                <div className="muted small">Attrition Probability</div>
                <div className="big-number" style={{ color: RISK_COLORS[e.risk_level] }}>
                  {e.attrition_probability != null ? `${Math.round(e.attrition_probability)}%` : "-"}
                </div>
              </div>
              <div>
                <div className="muted small">Risk Level</div>
                <RiskBadge level={e.risk_level} />
              </div>
            </div>
            <div className="muted small">Prediction</div>
            <p className="strong">{e.prediction || "Not scored yet"}</p>
            <p className="muted small">Last predicted: {formatDate(e.predicted_at)}</p>
          </div>

          <div className="card">
            <h3>Risk Factors</h3>
            <FactorList risk={e.risk_factors} protective={e.protective_factors} />
          </div>
        </div>
      </div>
    </>
  );
}
