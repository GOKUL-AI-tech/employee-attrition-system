import csv, io
from flask import Blueprint, jsonify, request, Response
from routes.auth import login_required
from routes.analytics import load, dept_stats

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/summary")
@login_required
def summary():
    df = load()
    n = len(df)
    pred_leave = int((df["probability"] >= 40).sum())
    high = df[df["risk_level"] == "High"].sort_values("probability", ascending=False)
    return jsonify(
        total=n, predicted_attrition=pred_leave,
        predicted_attrition_pct=round(pred_leave / n * 100, 1) if n else 0,
        actual_attrition=int((df["attrition"] == "Yes").sum()),
        attrition_pct=round(float((df["attrition"] == "Yes").mean() * 100), 1) if n else 0,
        high_risk_count=len(high),
        high_risk=high[["employee_id", "name", "department", "job_role", "probability"]].head(25).to_dict("records"),
        departments=dept_stats(df) if n else [])


@bp.get("/export")
@login_required
def export():
    kind = request.args.get("type", "employees")
    df = load()
    if kind == "risk":
        df = df.sort_values("probability", ascending=False)
        df["prediction"] = df["probability"].apply(lambda p: "Likely to Leave" if p >= 40 else "Likely to Stay")
        cols = ["employee_id", "name", "department", "job_role", "probability", "risk_level", "prediction"]
        df = df[cols].rename(columns={"probability": "attrition_probability_pct"})
    else:
        df = df.drop(columns=["id", "created_at"], errors="ignore")
    buf = io.StringIO()
    df.to_csv(buf, index=False, quoting=csv.QUOTE_NONNUMERIC)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={kind}_export.csv"})
