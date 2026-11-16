import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Alert, Loading, PageHeader, useLoad } from "../components/ui.jsx";
import { api } from "../services/api.js";

export default function Settings() {
  const { data, error, loading } = useLoad(api.settings);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState({ type: "success", text: "" });

  const retrain = async () => {
    setBusy(true);
    setMsg({ type: "success", text: "" });
    try {
      const m = await api.retrain();
      setMsg({ type: "success", text: `Model retrained and all employees re-scored. Accuracy on test data: ${(m.accuracy * 100).toFixed(1)}%.` });
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <Alert>{error}</Alert>;

  return (
    <>
      <PageHeader title="Settings" subtitle="Risk thresholds and model information" />
      <div className="two-col">
        <div className="card">
          <h3>Risk Thresholds</h3>
          <p className="muted small">Set in the backend (<code>LOW_RISK_MAX</code> and <code>MEDIUM_RISK_MAX</code> in <code>ml_model.py</code>, or as environment variables).</p>
          <ul className="threshold-list">
            <li><span className="badge badge-low">Low Risk</span> 0% - {data.low_risk_max}%</li>
            <li><span className="badge badge-medium">Medium Risk</span> {data.low_risk_max + 1}% - {data.medium_risk_max}%</li>
            <li><span className="badge badge-high">High Risk</span> {data.medium_risk_max + 1}% - 100%</li>
          </ul>
        </div>
        <div className="card">
          <h3>Model &amp; Data</h3>
          <dl className="profile-grid one">
            <div><dt>Algorithm</dt><dd>{data.model}</dd></div>
            <div><dt>Database</dt><dd>{data.database}</dd></div>
          </dl>
          <Alert type={msg.type}>{msg.text}</Alert>
          <button className="btn btn-primary" onClick={retrain} disabled={busy}>
            <RefreshCw size={16} className={busy ? "spin" : ""} /> {busy ? "Retraining..." : "Retrain model"}
          </button>
          <p className="muted small note">Retrains on dataset.csv and re-scores every employee (added to prediction history).</p>
        </div>
      </div>
    </>
  );
}
