import sqlite3
from flask import Blueprint, request, jsonify
from database import get_db, EMP_COLS
from routes.auth import login_required
from ml.generate_data import DEPT_ROLES
import ml_service

bp = Blueprint("employees", __name__, url_prefix="/api/employees")

RANGES = {"age": (16, 80), "monthly_income": (0, 1_000_000), "years_at_company": (0, 60),
          "job_satisfaction": (1, 4), "work_life_balance": (1, 4), "job_level": (1, 5),
          "performance_rating": (1, 4), "distance_from_home": (0, 500),
          "num_companies_worked": (0, 30), "training_times_last_year": (0, 50)}
CHOICES = {"gender": ["Male", "Female", "Other"], "overtime": ["Yes", "No"], "attrition": ["Yes", "No"]}


def clean(d):
    """Validate & normalise an employee payload. Returns (record, error)."""
    rec = {}
    for c in ("employee_id", "name", "department", "job_role"):
        v = str(d.get(c, "")).strip()
        if not v:
            return None, f"{c.replace('_', ' ').title()} is required"
        rec[c] = v
    for c, opts in CHOICES.items():
        v = d.get(c, "No" if c == "attrition" else "")
        if v not in opts:
            return None, f"{c.title()} must be one of {opts}"
        rec[c] = v
    for c, (lo, hi) in RANGES.items():
        try:
            v = float(d.get(c))
        except (TypeError, ValueError):
            return None, f"{c.replace('_', ' ').title()} must be a number"
        if not lo <= v <= hi:
            return None, f"{c.replace('_', ' ').title()} must be between {lo} and {hi}"
        rec[c] = int(v) if c not in ("monthly_income", "years_at_company", "distance_from_home") or v == int(v) else v
    return rec, None


@bp.get("/meta")
@login_required
def meta():
    return jsonify(departments=list(DEPT_ROLES), roles=DEPT_ROLES)


@bp.get("")
@login_required
def list_():
    q, dept = request.args.get("search", "").strip(), request.args.get("department", "").strip()
    sql = ("SELECT e.*, p.probability, p.risk_level, p.prediction FROM employees e "
           "LEFT JOIN predictions p ON p.employee_ref=e.id WHERE 1=1")
    args = []
    if q:
        sql += " AND (e.name LIKE ? OR e.employee_id LIKE ? OR e.job_role LIKE ?)"
        args += [f"%{q}%"] * 3
    if dept:
        sql += " AND e.department=?"
        args.append(dept)
    sql += " ORDER BY e.id DESC"
    return jsonify([dict(r) for r in get_db().execute(sql, args)])


@bp.post("")
@login_required
def create():
    rec, err = clean(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    db = get_db()
    try:
        cur = db.execute(f"INSERT INTO employees({','.join(EMP_COLS)}) VALUES({','.join('?' * len(EMP_COLS))})",
                         [rec[c] for c in EMP_COLS])
    except sqlite3.IntegrityError:
        return jsonify(error="Employee ID already exists"), 409
    db.commit()
    ml_service.score_employee(cur.lastrowid)
    return jsonify(id=cur.lastrowid), 201


@bp.put("/<int:eid>")
@login_required
def update(eid):
    rec, err = clean(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    db = get_db()
    try:
        cur = db.execute(f"UPDATE employees SET {','.join(c + '=?' for c in EMP_COLS)} WHERE id=?",
                         [rec[c] for c in EMP_COLS] + [eid])
    except sqlite3.IntegrityError:
        return jsonify(error="Employee ID already exists"), 409
    db.commit()
    if not cur.rowcount:
        return jsonify(error="Not found"), 404
    ml_service.score_employee(eid)
    return jsonify(ok=True)


@bp.delete("/<int:eid>")
@login_required
def delete(eid):
    db = get_db()
    db.execute("DELETE FROM predictions WHERE employee_ref=?", (eid,))
    cur = db.execute("DELETE FROM employees WHERE id=?", (eid,))
    db.commit()
    return (jsonify(ok=True), 200) if cur.rowcount else (jsonify(error="Not found"), 404)
