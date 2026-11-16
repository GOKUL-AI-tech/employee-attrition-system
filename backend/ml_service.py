"""Glue between Flask/SQLite and the ML module."""
import json, os
import pandas as pd
from database import get_db, EMP_COLS, BASE
from ml import attrition_model as am

MODEL_PATH = os.path.join(BASE, "model", "attrition_model.joblib")
_bundle = None


def _save(db, emp_ref, rec, res, replace=True):
    if replace and emp_ref is not None:
        db.execute("DELETE FROM predictions WHERE employee_ref=?", (emp_ref,))
    db.execute("INSERT INTO predictions(employee_ref,input_json,probability,prediction,risk_level,factors)"
               " VALUES(?,?,?,?,?,?)",
               (emp_ref, json.dumps(rec) if rec else None, res["probability"], res["prediction"],
                res["risk_level"], json.dumps(res.get("factors", []))))


def retrain():
    """Train on all employees in SQLite, save model, refresh every stored prediction."""
    global _bundle
    db = get_db()
    df = pd.read_sql_query("SELECT * FROM employees", db)
    _bundle, oof = am.train(df, MODEL_PATH)
    # stored risk uses out-of-fold probabilities so it isn't inflated by training-set memorisation
    db.execute("DELETE FROM predictions WHERE employee_ref IS NOT NULL")
    for (_, row), p in zip(df.iterrows(), oof):
        res = {"probability": round(float(p) * 100, 1),
               "prediction": "Likely to Leave" if p >= am.MEDIUM_MAX else "Likely to Stay",
               "risk_level": am.risk_level(float(p)), "factors": []}
        _save(db, int(row["id"]), None, res, replace=False)
    db.commit()
    return _bundle["metrics"]


def get_bundle():
    global _bundle
    if _bundle is None:
        if os.path.exists(MODEL_PATH):
            _bundle = am.load(MODEL_PATH)
        else:
            retrain()
    return _bundle


def ensure_ready():
    """Train on first run, or if predictions are missing."""
    db = get_db()
    if not os.path.exists(MODEL_PATH) or not db.execute(
            "SELECT 1 FROM predictions WHERE employee_ref IS NOT NULL").fetchone():
        retrain()
    else:
        get_bundle()


def predict_one(rec, explain=True):
    return am.predict(get_bundle(), [rec], explain=explain)[0]


def score_employee(emp_id):
    """(Re)compute and store the prediction for one employee row id."""
    db = get_db()
    row = db.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
    rec = {c: row[c] for c in EMP_COLS}
    res = predict_one(rec)
    _save(db, emp_id, rec, res)
    db.commit()
    return res


def model_info():
    b = get_bundle()
    return {"metrics": b["metrics"],
            "importances": [{"feature": am.LABELS[k], "importance": round(v * 100, 1)}
                            for k, v in b["importances"].items()],
            "model": "Random Forest (scikit-learn)"}
