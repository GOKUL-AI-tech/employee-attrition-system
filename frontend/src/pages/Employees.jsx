import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { PageHead, Panel, RiskBadge } from "../components/ui.jsx";

const EMPTY = { employee_id: "", name: "", age: 30, gender: "Male", department: "", job_role: "", monthly_income: 5000,
  years_at_company: 3, job_satisfaction: 3, work_life_balance: 3, overtime: "No", job_level: 2, performance_rating: 3,
  distance_from_home: 10, num_companies_worked: 1, training_times_last_year: 2, attrition: "No" };

export const NUM_FIELDS = [
  ["age", "Age"], ["monthly_income", "Monthly Income"], ["years_at_company", "Years at Company"],
  ["distance_from_home", "Distance From Home (km)"], ["num_companies_worked", "Companies Worked"],
  ["training_times_last_year", "Training Times Last Year"],
];
export const SCALE_FIELDS = [
  ["job_satisfaction", "Job Satisfaction (1-4)", 4], ["work_life_balance", "Work-Life Balance (1-4)", 4],
  ["job_level", "Job Level (1-5)", 5], ["performance_rating", "Performance Rating (1-4)", 4],
];

export function EmployeeFields({ f, set, meta, showIdentity = true, showAttrition = true }) {
  const roles = meta.roles[f.department] || [];
  const ch = (k) => (e) => set({ ...f, [k]: e.target.value, ...(k === "department" ? { job_role: "" } : {}) });
  return (
    <div className="form-grid">
      {showIdentity && <>
        <label>Employee ID<input value={f.employee_id} onChange={ch("employee_id")} required /></label>
        <label>Name<input value={f.name} onChange={ch("name")} required /></label>
      </>}
      <label>Gender<select value={f.gender} onChange={ch("gender")}><option>Male</option><option>Female</option><option>Other</option></select></label>
      <label>Department<select value={f.department} onChange={ch("department")} required>
        <option value="">Select…</option>{meta.departments.map((d) => <option key={d}>{d}</option>)}</select></label>
      <label>Job Role<select value={f.job_role} onChange={ch("job_role")} required>
        <option value="">Select…</option>
        {f.job_role && !roles.includes(f.job_role) && <option>{f.job_role}</option>}
        {roles.map((r) => <option key={r}>{r}</option>)}</select></label>
      {NUM_FIELDS.map(([k, l]) => <label key={k}>{l}<input type="number" min="0" step="any" value={f[k]} onChange={ch(k)} required /></label>)}
      {SCALE_FIELDS.map(([k, l, max]) => <label key={k}>{l}
        <select value={f[k]} onChange={ch(k)}>{Array.from({ length: max }, (_, i) => i + 1).map((n) => <option key={n}>{n}</option>)}</select></label>)}
      <label>Overtime<select value={f.overtime} onChange={ch("overtime")}><option>No</option><option>Yes</option></select></label>
      {showAttrition && <label>Left the company?<select value={f.attrition} onChange={ch("attrition")}><option>No</option><option>Yes</option></select></label>}
    </div>
  );
}

export default function Employees() {
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState({ departments: [], roles: {} });
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState("");
  const [form, setForm] = useState(null); // {id?, ...fields}
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.get(`/employees?search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}`).then(setRows).catch((e) => setErr(e.message));
  }, [search, dept]);
  useEffect(() => { api.get("/employees/meta").then(setMeta); }, []);
  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [load]);

  const save = async (e) => {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      form.id ? await api.put(`/employees/${form.id}`, form) : await api.post("/employees", form);
      setForm(null); load();
    } catch (x) { setErr(x.message); } finally { setBusy(false); }
  };
  const remove = async (r) => {
    if (!window.confirm(`Delete ${r.name} (${r.employee_id})?`)) return;
    await api.del(`/employees/${r.id}`); load();
  };

  return (
    <>
      <PageHead title="Employees" sub={`${rows.length} employees`}>
        <button className="btn primary" onClick={() => { setErr(""); setForm({ ...EMPTY }); }}>+ Add Employee</button>
      </PageHead>
      <Panel title="Employee Directory">
        <div className="toolbar">
          <input placeholder="Search name, ID or role…" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={dept} onChange={(e) => setDept(e.target.value)}>
            <option value="">All departments</option>{meta.departments.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        {err && !form && <div className="alert">{err}</div>}
        <div className="table-wrap tall"><table>
          <thead><tr><th>ID</th><th>Name</th><th>Dept</th><th>Role</th><th>Age</th><th>Income</th><th>Yrs</th><th>OT</th><th>Risk</th><th></th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.risk_level === "High" ? "row-high" : ""}>
                <td>{r.employee_id}</td><td>{r.name}</td><td>{r.department}</td><td>{r.job_role}</td><td>{r.age}</td>
                <td>${Math.round(r.monthly_income).toLocaleString()}</td><td>{r.years_at_company}</td><td>{r.overtime}</td>
                <td>{r.risk_level && <><RiskBadge level={r.risk_level} /> <span className="muted small">{r.probability}%</span></>}</td>
                <td className="nowrap">
                  <button className="btn sm" onClick={() => { setErr(""); setForm({ ...r }); }}>Edit</button>{" "}
                  <button className="btn sm danger" onClick={() => remove(r)}>Delete</button>
                </td>
              </tr>))}
            {!rows.length && <tr><td colSpan="10" className="muted center">No employees found</td></tr>}
          </tbody>
        </table></div>
      </Panel>

      {form && (
        <div className="modal-bg" onMouseDown={(e) => e.target === e.currentTarget && setForm(null)}>
          <form className="modal" onSubmit={save}>
            <h2>{form.id ? "Edit Employee" : "Add Employee"}</h2>
            {err && <div className="alert">{err}</div>}
            <EmployeeFields f={form} set={setForm} meta={meta} />
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setForm(null)}>Cancel</button>
              <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
