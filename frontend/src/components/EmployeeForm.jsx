import { useState } from "react";

const LABELS = {
  age: "Age", gender: "Gender", department: "Department", job_role: "Job Role",
  monthly_income: "Monthly Income ($)", years_at_company: "Years at Company",
  job_satisfaction: "Job Satisfaction (1-4)", work_life_balance: "Work-Life Balance (1-4)",
  overtime: "Overtime", distance_from_home: "Distance From Home (km)", job_level: "Job Level (1-5)",
  performance_rating: "Performance Rating (1-4)", num_companies_worked: "Companies Worked",
  total_working_years: "Total Working Years", training_times: "Training Times Last Year",
  marital_status: "Marital Status", business_travel: "Business Travel",
};

const SELECT_FIELDS = ["gender", "department", "job_role", "overtime", "marital_status", "business_travel"];
const NUMBER_FIELDS = [
  "age", "monthly_income", "years_at_company", "job_satisfaction", "work_life_balance",
  "distance_from_home", "job_level", "performance_rating", "num_companies_worked",
  "total_working_years", "training_times",
];

export const EMPTY_EMPLOYEE = {
  employee_id: "", name: "", age: "", gender: "Male", department: "Sales", job_role: "Sales Executive",
  monthly_income: "", years_at_company: "", job_satisfaction: 3, work_life_balance: 3, overtime: "No",
  distance_from_home: "", job_level: 1, performance_rating: 3, num_companies_worked: "",
  total_working_years: "", training_times: "", marital_status: "Single", business_travel: "Travel_Rarely",
};

const pretty = (v) => v.replace(/_/g, " ");

// Shared by the Employees page (add/edit) and the Predict page.
export default function EmployeeForm({ initial, options, errors = {}, onSubmit, submitLabel, busy, extra, nameRequired = true }) {
  const [values, setValues] = useState({ ...EMPTY_EMPLOYEE, ...initial });
  const set = (key) => (e) => setValues((v) => ({ ...v, [key]: e.target.value }));

  const field = (key, label, input) => (
    <label className={"field" + (errors[key] ? " has-error" : "")} key={key}>
      <span>{label}</span>
      {input}
      {errors[key] && <em>{errors[key]}</em>}
    </label>
  );

  return (
    <form
      className="form"
      noValidate
      onSubmit={(e) => { e.preventDefault(); onSubmit(values); }}
    >
      <div className="form-grid">
        {field("employee_id", "Employee ID", (
          <input value={values.employee_id} onChange={set("employee_id")} placeholder="EMP001" />
        ))}
        {field("name", nameRequired ? "Name" : "Name (optional)", (
          <input value={values.name} onChange={set("name")} placeholder="Full name" />
        ))}
        {SELECT_FIELDS.map((key) => field(key, LABELS[key], (
          <select value={values[key]} onChange={set(key)}>
            {(options?.choices[key] || []).map((o) => <option key={o} value={o}>{pretty(o)}</option>)}
          </select>
        )))}
        {NUMBER_FIELDS.map((key) => {
          const [min, max] = options?.ranges[key] || [];
          return field(key, LABELS[key], (
            <input type="number" inputMode="numeric" min={min} max={max} value={values[key]} onChange={set(key)} />
          ));
        })}
      </div>
      {extra}
      <div className="form-actions">
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Working..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
