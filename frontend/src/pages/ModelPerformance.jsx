import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Alert, Loading, PageHeader, useLoad } from "../components/ui.jsx";
import { api } from "../services/api.js";

const pct = (v) => `${(v * 100).toFixed(1)}%`;

export default function ModelPerformance() {
  const { data: m, error, loading } = useLoad(api.metrics);
  if (loading) return <Loading />;
  if (error) return <Alert>{error}</Alert>;

  const cm = m.confusion_matrix;
  const top = m.feature_importance.slice(0, 10);
  const maxCell = Math.max(cm.tn, cm.fp, cm.fn, cm.tp, 1);
  const cell = (v, good) => ({
    background: `${good ? "rgba(16,185,129," : "rgba(239,68,68,"}${0.12 + 0.55 * (v / maxCell)})`,
  });

  return (
    <>
      <PageHeader title="Model Performance" subtitle={m.algorithm} />

      <div className="kpi-grid four">
        {[["Accuracy", m.accuracy], ["Precision", m.precision], ["Recall", m.recall], ["F1 Score", m.f1]].map(([label, v]) => (
          <div className="card metric" key={label}>
            <div className="kpi-label">{label}</div>
            <div className="kpi-value">{pct(v)}</div>
          </div>
        ))}
      </div>

      <Alert type="info">
        Measured on {m.dataset.test_rows} held-out test employees (20% of {m.dataset.rows}; the other 80% was used for training).
        {" "}{m.dataset.source}. Only {pct(m.dataset.attrition_rate)} of employees in the data left, so precision is the weakest score —
        treat predictions as a screening aid, not a verdict. Metrics describe the "Yes/No leaves" classification at a 50% cut-off.
      </Alert>

      <div className="two-col">
        <div className="card">
          <h3>Confusion Matrix</h3>
          <p className="muted small">Test set. Rows = actual, columns = predicted.</p>
          <table className="cm">
            <thead><tr><th></th><th>Predicted: Stays</th><th>Predicted: Leaves</th></tr></thead>
            <tbody>
              <tr><th>Actual: Stayed</th><td style={cell(cm.tn, true)}><b>{cm.tn}</b><small>True negative</small></td><td style={cell(cm.fp, false)}><b>{cm.fp}</b><small>False positive</small></td></tr>
              <tr><th>Actual: Left</th><td style={cell(cm.fn, false)}><b>{cm.fn}</b><small>False negative</small></td><td style={cell(cm.tp, true)}><b>{cm.tp}</b><small>True positive</small></td></tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>Feature Importance</h3>
          <p className="muted small">Calculated from the trained model (permutation importance on the test set). Top 10 shown.</p>
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={top} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid stroke="#e5e7eb" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 12, fill: "#6b7280" }} />
              <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 12, fill: "#6b7280" }} />
              <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
              <Bar dataKey="importance" name="Importance" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
