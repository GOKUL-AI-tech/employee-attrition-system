import json
from flask import Blueprint, request, jsonify
from database import get_db
from routes.auth import login_required
from routes.employees import clean
import ml_service

bp = Blueprint("predict", __name__, url_prefix="/api")


@bp.post("/predict")
@login_required
def predict():
    d = request.get_json(silent=True) or {}
    d.setdefault("employee_id", "ADHOC"); d.setdefault("name", "Ad-hoc"); d.setdefault("attrition", "No")
    rec, err = clean(d)
    if err:
        return jsonify(error=err), 400
    res = ml_service.predict_one(rec)
    db = get_db()
    ml_service._save(db, None, rec, res, replace=False)  # history of manual predictions
    db.commit()
    return jsonify(res)


@bp.get("/predict/history")
@login_required
def history():
    rows = get_db().execute("SELECT * FROM predictions WHERE employee_ref IS NULL ORDER BY id DESC LIMIT 15").fetchall()
    out = []
    for r in rows:
        inp = json.loads(r["input_json"] or "{}")
        out.append({"id": r["id"], "created_at": r["created_at"], "department": inp.get("department"),
                    "job_role": inp.get("job_role"), "probability": r["probability"],
                    "risk_level": r["risk_level"], "prediction": r["prediction"]})
    return jsonify(out)


@bp.get("/risk")
@login_required
def risk():
    level = request.args.get("level", "")
    sql = ("SELECT e.id, e.employee_id, e.name, e.department, e.job_role, p.probability, p.risk_level, p.prediction "
           "FROM employees e JOIN predictions p ON p.employee_ref=e.id")
    args = []
    if level in ("Low", "Medium", "High"):
        sql += " WHERE p.risk_level=?"; args.append(level)
    sql += " ORDER BY p.probability DESC"
    return jsonify([dict(r) for r in get_db().execute(sql, args)])


@bp.get("/employees/<int:eid>/factors")
@login_required
def factors(eid):
    r = get_db().execute("SELECT factors FROM predictions WHERE employee_ref=?", (eid,)).fetchone()
    f = json.loads(r["factors"]) if r and r["factors"] else []
    if not f:
        f = ml_service.score_employee(eid)["factors"]
    return jsonify(f)


@bp.get("/model/info")
@login_required
def info():
    return jsonify(ml_service.model_info())


@bp.post("/model/retrain")
@login_required
def retrain():
    try:
        return jsonify(metrics=ml_service.retrain())
    except ValueError as e:
        return jsonify(error=str(e)), 400
