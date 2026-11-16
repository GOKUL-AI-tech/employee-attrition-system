import pandas as pd
from flask import Blueprint, jsonify
from database import get_db
from routes.auth import login_required

bp = Blueprint("analytics", __name__, url_prefix="/api")


def load():
    return pd.read_sql_query(
        "SELECT e.*, p.probability, p.risk_level FROM employees e LEFT JOIN predictions p ON p.employee_ref=e.id",
        get_db())


def group(df, col):
    df = df.assign(left=(df["attrition"] == "Yes").astype(int))
    g = df.groupby(col, observed=True).agg(total=("left", "size"), left=("left", "sum")).reset_index()
    g["rate"] = (g["left"] / g["total"] * 100).round(1)
    g = g.rename(columns={col: "name"})
    g["name"] = g["name"].astype(str)
    return g.to_dict("records")


def dept_stats(df):
    out = []
    for name, s in df.groupby("department"):
        left = int((s["attrition"] == "Yes").sum())
        out.append({"department": name, "total": len(s), "left": left,
                    "rate": round(left / len(s) * 100, 1),
                    "high_risk": int((s["risk_level"] == "High").sum()),
                    "avg_salary": round(float(s["monthly_income"].mean()), 0),
                    "avg_satisfaction": round(float(s["job_satisfaction"].mean()), 2)})
    return out


@bp.get("/dashboard")
@login_required
def dashboard():
    df = load()
    n = len(df)
    if n == 0:
        return jsonify(empty=True)
    dist = df["risk_level"].fillna("Low").value_counts()
    at_risk = int(dist.get("High", 0))
    top = df[df["risk_level"] == "High"].sort_values("probability", ascending=False).head(6)
    return jsonify(
        empty=False, total=n, at_risk=at_risk, medium_risk=int(dist.get("Medium", 0)), low_risk=int(dist.get("Low", 0)),
        high_risk=int(dist.get("High", 0)),
        attrition_rate=round(float((df["attrition"] == "Yes").mean() * 100), 1),
        avg_salary=round(float(df["monthly_income"].mean()), 0),
        avg_satisfaction=round(float(df["job_satisfaction"].mean()), 2),
        departments=dept_stats(df),
        risk_distribution=[{"name": k, "value": int(dist.get(k, 0))} for k in ("Low", "Medium", "High")],
        top_risk=top[["id", "employee_id", "name", "department", "job_role", "probability", "risk_level"]].to_dict("records"))


@bp.get("/analytics")
@login_required
def analytics():
    df = load()
    if df.empty:
        return jsonify({})
    df["age_group"] = pd.cut(df["age"], [0, 24, 34, 44, 54, 200], labels=["<25", "25-34", "35-44", "45-54", "55+"])
    df["salary_range"] = pd.cut(df["monthly_income"], [-1, 3000, 5000, 8000, 12000, 1e12],
                                labels=["<3k", "3k-5k", "5k-8k", "8k-12k", "12k+"])
    df["tenure"] = pd.cut(df["years_at_company"], [-1, 1, 3, 6, 10, 100], labels=["0-1", "2-3", "4-6", "7-10", "10+"])
    df["satisfaction"] = df["job_satisfaction"].map({1: "1 - Low", 2: "2 - Medium", 3: "3 - High", 4: "4 - Very High"})
    df["ot"] = df["overtime"].map({"Yes": "Overtime", "No": "No Overtime"})
    return jsonify(
        department=group(df, "department"), job_role=group(df, "job_role"), age_group=group(df, "age_group"),
        salary_range=group(df, "salary_range"), overtime=group(df, "ot"),
        satisfaction=group(df, "satisfaction"), tenure=group(df, "tenure"))
