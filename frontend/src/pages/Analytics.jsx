import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { COLORS, PageHead, Panel } from "../components/ui.jsx";

function Chart({ title, data, horizontal }) {
  const h = horizontal ? Math.max(260, data.length * 34) : 260;
  return (
    <Panel title={title}>
      <ResponsiveContainer width="100%" height={h}>
        <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ left: horizontal ? 40 : -10 }}>
          <CartesianGrid stroke={COLORS.grid} vertical={horizontal} horizontal={!horizontal} />
          {horizontal ? <><XAxis type="number" unit="%" /><YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} /></>
            : <><XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} /><YAxis unit="%" /></>}
          <Tooltip formatter={(v, n, p) => [v + "%  (" + p.payload.left + " of " + p.payload.total + " left)", "Attrition rate"]} />
          <Bar dataKey="rate" name="Attrition rate" fill={COLORS.blue} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Panel>
  );
}

export default function Analytics() {
  const [a, setA] = useState(null);
  useEffect(() => { api.get("/analytics").then(setA); }, []);
  if (!a) return <p className="muted">Loading…</p>;
  return (
    <>
      <PageHead title="HR Analytics" sub="Attrition rate (% of employees who left) across key dimensions" />
      <div className="grid two">
        <Chart title="Attrition by Department" data={a.department} />
        <Chart title="Attrition by Age Group" data={a.age_group} />
        <Chart title="Attrition by Salary Range (monthly)" data={a.salary_range} />
        <Chart title="Attrition vs Overtime" data={a.overtime} />
        <Chart title="Attrition vs Job Satisfaction" data={a.satisfaction} />
        <Chart title="Attrition vs Years at Company" data={a.tenure} />
      </div>
      <Chart title="Attrition by Job Role" data={[...a.job_role].sort((x, y) => y.rate - x.rate)} horizontal />
    </>
  );
}
