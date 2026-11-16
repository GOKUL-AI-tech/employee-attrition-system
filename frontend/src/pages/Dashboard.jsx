import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { Card, COLORS, money, PageHead, Panel, RISK_COLORS, RiskBadge } from "../components/ui.jsx";

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.get("/dashboard").then(setD).catch((e) => setErr(e.message)); }, []);
  if (err) return <div className="alert">{err}</div>;
  if (!d) return <p className="muted">Loading…</p>;
  if (d.empty) return <p className="muted">No employees yet. Add some on the Employees page.</p>;
  return (
    <>
      <PageHead title="HR Dashboard" sub="Workforce overview and predicted attrition risk" />
      <div className="grid cards">
        <Card label="Total Employees" value={d.total} />
        <Card label="Employees at Risk" value={d.at_risk} sub={`High risk · ${d.medium_risk} medium`} tone="danger" />
        <Card label="Low Risk" value={d.low_risk} tone="good" />
        <Card label="Attrition Rate" value={d.attrition_rate + "%"} />
        <Card label="Average Salary" value={money(d.avg_salary)} sub="per month" />
        <Card label="Avg Job Satisfaction" value={d.avg_satisfaction + " / 4"} />
      </div>
      <div className="grid two">
        <Panel title="Employees by Department">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={d.departments} margin={{ left: -10 }}>
              <CartesianGrid stroke={COLORS.grid} vertical={false} />
              <XAxis dataKey="department" tick={{ fontSize: 11 }} interval={0} /><YAxis allowDecimals={false} />
              <Tooltip /><Bar dataKey="total" name="Employees" fill={COLORS.blue} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Attrition by Department">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={d.departments} margin={{ left: -10 }}>
              <CartesianGrid stroke={COLORS.grid} vertical={false} />
              <XAxis dataKey="department" tick={{ fontSize: 11 }} interval={0} /><YAxis allowDecimals={false} />
              <Tooltip /><Bar dataKey="left" name="Left company" fill={COLORS.high} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>
      <div className="grid two">
        <Panel title="Attrition Risk Distribution">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={d.risk_distribution} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2} label>
                {d.risk_distribution.map((r) => <Cell key={r.name} fill={RISK_COLORS[r.name]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Highest-Risk Employees">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Employee</th><th>Department</th><th>Prob.</th><th>Risk</th></tr></thead>
              <tbody>{d.top_risk.map((e) => (
                <tr key={e.id} className="row-high"><td>{e.name}<div className="muted small">{e.employee_id}</div></td>
                  <td>{e.department}</td><td><b>{e.probability}%</b></td><td><RiskBadge level={e.risk_level} /></td></tr>))}</tbody>
            </table>
          </div>
        </Panel>
      </div>
      <Panel title="Department Summary">
        <div className="table-wrap"><table>
          <thead><tr><th>Department</th><th>Employees</th><th>Left</th><th>Attrition</th><th>High Risk</th><th>Avg Salary</th><th>Avg Satisfaction</th></tr></thead>
          <tbody>{d.departments.map((x) => (<tr key={x.department}><td>{x.department}</td><td>{x.total}</td><td>{x.left}</td>
            <td>{x.rate}%</td><td>{x.high_risk}</td><td>{money(x.avg_salary)}</td><td>{x.avg_satisfaction}</td></tr>))}</tbody>
        </table></div>
      </Panel>
    </>
  );
}
