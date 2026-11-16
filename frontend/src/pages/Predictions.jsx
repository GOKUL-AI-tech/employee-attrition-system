import { Link } from "react-router-dom";
import { Alert, Loading, PageHeader, RiskBadge, formatDate, useLoad } from "../components/ui.jsx";
import { api } from "../services/api.js";

export default function Predictions() {
  const { data, error, loading } = useLoad(api.predictions);
  return (
    <>
      <PageHeader title="Predictions" subtitle="History of every prediction made by the model (newest first)" />
      {error && <Alert>{error}</Alert>}
      {loading ? <Loading /> : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Employee ID</th><th>Name</th><th>Department</th><th className="num">Probability</th><th>Risk Level</th><th>Prediction</th><th>Predicted At</th></tr>
              </thead>
              <tbody>
                {(data || []).map((p) => (
                  <tr key={p.id}>
                    <td className="mono">{p.employee_id}</td>
                    <td>{p.name || <span className="muted">Not in records</span>}</td>
                    <td>{p.department || "-"}</td>
                    <td className="num">{Math.round(p.attrition_probability)}%</td>
                    <td><RiskBadge level={p.risk_level} /></td>
                    <td>{p.prediction}</td>
                    <td>{formatDate(p.predicted_at)}</td>
                  </tr>
                ))}
                {data?.length === 0 && <tr><td colSpan={7} className="empty">No predictions yet. Try the <Link to="/predict">Predict Attrition</Link> page.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
