"""All API endpoints (one Flask blueprint)."""
import os
import secrets
import sqlite3
from collections import defaultdict

from flask import Blueprint, jsonify, request

import ml_model
from database import SAMPLE_COLUMNS, get_conn
from models import CHOICES, FEATURES, NUMERIC_RANGES, validate_employee

api = Blueprint("api", __name__, url_prefix="/api")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
_tokens = set()  # demo-grade auth: tokens live in memory until the server restarts

OPEN_ENDPOINTS = {"api.login", "api.health"}
EMPLOYEE_COLUMNS = ["employee_id", "name"] + [c for c in SAMPLE_COLUMNS if c not in ("employee_id", "name")]

LATEST_PREDICTION_JOIN = """
    LEFT JOIN predictions p ON p.id = (
        SELECT MAX(id) FROM predictions WHERE employee_id = e.employee_id)
"""
EMPLOYEE_SELECT = """
    SELECT e.*, p.attrition_probability, p.risk_level, p.prediction, p.predicted_at
    FROM employees e
""" + LATEST_PREDICTION_JOIN


def error(message, status=400, fields=None):
    body = {"error": message}
    if fields:
        body["fields"] = fields
    return jsonify(body), status


@api.before_request
def require_login():
    if request.method == "OPTIONS" or request.endpoint in OPEN_ENDPOINTS:
        return None
    token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    if token not in _tokens:
        return error("Please log in to continue.", 401)
    return None


def features_of(row):
    return {f: row[f] for f in FEATURES}


def store_prediction(conn, employee_id, features):
    """Run the model, save the result in the predictions table, return the result dict."""
    result = ml_model.predict(features)
    cur = conn.execute(
        "INSERT INTO predictions (employee_id, attrition_probability, risk_level, prediction) "
        "VALUES (?, ?, ?, ?)",
        (employee_id, result["probability"], result["risk_level"], result["prediction"]))
    result["predicted_at"] = conn.execute(
        "SELECT predicted_at FROM predictions WHERE id = ?", (cur.lastrowid,)).fetchone()[0]
    return result


def rescore_all(conn):
    rows = conn.execute("SELECT * FROM employees").fetchall()
    probs = ml_model.predict_many([features_of(r) for r in rows])
    for r, p in zip(rows, probs):
        percent = int(round(p * 100))
        risk = ml_model.classify_risk(percent)
        conn.execute(
            "INSERT INTO predictions (employee_id, attrition_probability, risk_level, prediction) "
            "VALUES (?, ?, ?, ?)",
            (r["employee_id"], percent, risk, ml_model.RISK_TO_PREDICTION[risk]))


def fetch_employee(conn, pk):
    return conn.execute(EMPLOYEE_SELECT + " WHERE e.id = ?", (pk,)).fetchone()


# --------------------------------------------------------------------- misc
@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASSWORD:
        token = secrets.token_hex(24)
        _tokens.add(token)
        return jsonify({"token": token, "user": {"username": ADMIN_USER, "role": "HR Admin"}})
    return error("Incorrect username or password.", 401)


@api.post("/logout")
def logout():
    _tokens.discard(request.headers.get("Authorization", "").replace("Bearer ", "", 1))
    return jsonify({"ok": True})


@api.get("/options")
def options():
    return jsonify({"choices": CHOICES, "ranges": NUMERIC_RANGES})


# ---------------------------------------------------------------- employees
@api.get("/employees")
def list_employees():
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    risk = request.args.get("risk", "").strip()

    where, params = [], []
    if search:
        where.append("(e.name LIKE ? OR e.employee_id LIKE ? OR e.job_role LIKE ?)")
        params += [f"%{search}%"] * 3
    if department:
        where.append("e.department = ?")
        params.append(department)
    if risk:
        where.append("p.risk_level = ?")
        params.append(risk)
    sql = EMPLOYEE_SELECT + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY e.employee_id"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@api.get("/employees/<int:pk>")
def get_employee(pk):
    with get_conn() as conn:
        row = fetch_employee(conn, pk)
    if row is None:
        return error("Employee not found.", 404)
    employee = dict(row)
    # Fresh explanation for the detail view (percent comes from the stored prediction)
    result = ml_model.predict(features_of(row))
    employee["risk_factors"] = result["risk_factors"]
    employee["protective_factors"] = result["protective_factors"]
    employee["disclaimer"] = result["disclaimer"]
    return jsonify(employee)


@api.post("/employees")
def create_employee():
    clean, errors = validate_employee(request.get_json(silent=True))
    if errors:
        return error("Please fix the highlighted fields.", 400, errors)
    try:
        with get_conn() as conn:
            cols = ",".join(clean)
            cur = conn.execute(
                f"INSERT INTO employees ({cols}) VALUES ({','.join('?' * len(clean))})",
                list(clean.values()))
            store_prediction(conn, clean["employee_id"], clean)
            row = fetch_employee(conn, cur.lastrowid)
    except sqlite3.IntegrityError:
        return error("An employee with this Employee ID already exists.", 409,
                     {"employee_id": "This Employee ID is already in use."})
    return jsonify(dict(row)), 201


@api.put("/employees/<int:pk>")
def update_employee(pk):
    clean, errors = validate_employee(request.get_json(silent=True))
    if errors:
        return error("Please fix the highlighted fields.", 400, errors)
    try:
        with get_conn() as conn:
            old = conn.execute("SELECT employee_id FROM employees WHERE id = ?", (pk,)).fetchone()
            if old is None:
                return error("Employee not found.", 404)
            sets = ",".join(f"{k} = ?" for k in clean)
            conn.execute(f"UPDATE employees SET {sets} WHERE id = ?", list(clean.values()) + [pk])
            if old["employee_id"] != clean["employee_id"]:
                conn.execute("UPDATE predictions SET employee_id = ? WHERE employee_id = ?",
                             (clean["employee_id"], old["employee_id"]))
            store_prediction(conn, clean["employee_id"], clean)  # re-score with the new details
            row = fetch_employee(conn, pk)
    except sqlite3.IntegrityError:
        return error("An employee with this Employee ID already exists.", 409,
                     {"employee_id": "This Employee ID is already in use."})
    return jsonify(dict(row))


@api.delete("/employees/<int:pk>")
def delete_employee(pk):
    with get_conn() as conn:
        row = conn.execute("SELECT employee_id FROM employees WHERE id = ?", (pk,)).fetchone()
        if row is None:
            return error("Employee not found.", 404)
        conn.execute("DELETE FROM predictions WHERE employee_id = ?", (row["employee_id"],))
        conn.execute("DELETE FROM employees WHERE id = ?", (pk,))
    return jsonify({"ok": True})


# --------------------------------------------------------------- prediction
@api.post("/predict")
def predict():
    data = request.get_json(silent=True)
    clean, errors = validate_employee(data, require_identity=False)
    employee_id = str((data or {}).get("employee_id", "") or "").strip()
    name = str((data or {}).get("name", "") or "").strip()
    save = bool((data or {}).get("save_employee"))
    if not employee_id:
        errors["employee_id"] = "Employee ID is required."
    if save and not name:
        errors["name"] = "Name is required to save the employee."
    if errors:
        return error("Please fix the highlighted fields.", 400, errors)

    try:
        with get_conn() as conn:
            if save:  # create or update the employee record with these details
                exists = conn.execute("SELECT id FROM employees WHERE employee_id = ?",
                                      (employee_id,)).fetchone()
                record = {"employee_id": employee_id, "name": name, **clean}
                if exists:
                    sets = ",".join(f"{k} = ?" for k in record)
                    conn.execute(f"UPDATE employees SET {sets} WHERE id = ?",
                                 list(record.values()) + [exists["id"]])
                else:
                    conn.execute(
                        f"INSERT INTO employees ({','.join(record)}) VALUES ({','.join('?' * len(record))})",
                        list(record.values()))
            result = store_prediction(conn, employee_id, clean)
    except sqlite3.Error:
        return error("Could not save the prediction. Please try again.", 500)
    result["employee_id"] = employee_id
    result["saved_to_employees"] = save
    return jsonify(result)


@api.get("/predictions")
def list_predictions():
    limit = min(request.args.get("limit", 200, type=int), 1000)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT pr.*, e.name, e.department FROM predictions pr "
            "LEFT JOIN employees e ON e.employee_id = pr.employee_id "
            "ORDER BY pr.id DESC LIMIT ?", (limit,)).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------- dashboard
def tenure_bucket(years):
    if years < 2:
        return "0-1 yrs"
    if years < 5:
        return "2-4 yrs"
    if years < 10:
        return "5-9 yrs"
    return "10+ yrs"


@api.get("/dashboard")
def dashboard():
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT e.department, e.job_role, e.overtime, e.years_at_company, "
            "p.attrition_probability AS prob, p.risk_level AS risk FROM employees e"
            + LATEST_PREDICTION_JOIN).fetchall()]
    rows = [r for r in rows if r["risk"]]

    def avg(values):
        return round(sum(values) / len(values), 1) if values else 0

    counts = {lvl: sum(1 for r in rows if r["risk"] == lvl) for lvl in ("Low", "Medium", "High")}

    by_dept = defaultdict(lambda: {"Low": 0, "Medium": 0, "High": 0})
    by_role, by_ot, by_tenure = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in rows:
        by_dept[r["department"]][r["risk"]] += 1
        by_role[r["job_role"]].append(r["prob"])
        by_ot["Overtime" if r["overtime"] == "Yes" else "No overtime"].append(r["prob"])
        by_tenure[tenure_bucket(r["years_at_company"])].append(r["prob"])

    tenure_order = ["0-1 yrs", "2-4 yrs", "5-9 yrs", "10+ yrs"]
    return jsonify({
        "kpis": {
            "total": len(rows), "high": counts["High"], "medium": counts["Medium"],
            "low": counts["Low"], "average_risk": avg([r["prob"] for r in rows]),
        },
        "risk_distribution": [{"name": k, "value": v} for k, v in counts.items()],
        "department_risk": [{"department": d, **v} for d, v in sorted(by_dept.items())],
        "role_risk": sorted(
            [{"role": k, "avg_risk": avg(v), "count": len(v)} for k, v in by_role.items()],
            key=lambda d: d["avg_risk"], reverse=True),
        "overtime_risk": [{"group": k, "avg_risk": avg(v), "count": len(v)}
                          for k, v in sorted(by_ot.items(), reverse=True)],
        "tenure_risk": [{"group": k, "avg_risk": avg(by_tenure[k]), "count": len(by_tenure[k])}
                        for k in tenure_order if k in by_tenure],
    })


# -------------------------------------------------------- model / settings
@api.get("/model-metrics")
def model_metrics():
    return jsonify(ml_model.get_metrics())


@api.get("/settings")
def get_settings():
    return jsonify({**ml_model.settings(), "model": ml_model.get_metrics()["algorithm"],
                    "database": "employee_attrition.db (SQLite)"})


@api.post("/retrain")
def retrain():
    ml_model.train_model()
    with get_conn() as conn:
        rescore_all(conn)
    return jsonify(ml_model.get_metrics())
