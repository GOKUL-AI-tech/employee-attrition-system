"""Core ML logic: preprocessing, training, prediction, explanations."""
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CAT = ["gender", "department", "job_role", "overtime"]
NUM = ["age", "monthly_income", "years_at_company", "job_satisfaction",
       "work_life_balance", "job_level", "performance_rating",
       "distance_from_home", "num_companies_worked", "training_times_last_year"]
FEATURES = CAT + NUM

LABELS = {
    "gender": "Gender", "department": "Department", "job_role": "Job Role",
    "overtime": "Overtime", "age": "Age", "monthly_income": "Monthly Income",
    "years_at_company": "Years at Company", "job_satisfaction": "Job Satisfaction",
    "work_life_balance": "Work-Life Balance", "job_level": "Job Level",
    "performance_rating": "Performance Rating", "distance_from_home": "Distance From Home",
    "num_companies_worked": "Companies Worked", "training_times_last_year": "Training Times Last Year",
}
LOW_MAX, MEDIUM_MAX = 0.20, 0.40  # <20% Low, <40% Medium, else High (High = likely to leave)


def risk_level(p: float) -> str:
    return "Low" if p < LOW_MAX else "Medium" if p < MEDIUM_MAX else "High"


def _pipeline():
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", StandardScaler(), NUM),
    ])
    clf = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=5,
                                 random_state=42, n_jobs=-1)
    return Pipeline([("pre", pre), ("clf", clf)])


def _frame(records):
    df = pd.DataFrame(records)[FEATURES].copy()
    for c in NUM:
        df[c] = pd.to_numeric(df[c])
    return df


def train(df: pd.DataFrame, path: str):
    """Train on a DataFrame having FEATURES + 'attrition' (Yes/No).
    Returns (bundle, out_of_fold_probabilities). Saves bundle to `path`."""
    X = _frame(df)
    y = (df["attrition"].astype(str).str.lower() == "yes").astype(int).values
    if len(np.unique(y)) < 2 or len(y) < 30:
        raise ValueError("Need at least 30 employees with both Yes and No attrition values to train.")
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    oof = cross_val_predict(_pipeline(), X, y, cv=cv, method="predict_proba")[:, 1]
    pipe = _pipeline().fit(X, y)

    # global importance aggregated back to original features
    names = pipe.named_steps["pre"].get_feature_names_out()
    imp = pipe.named_steps["clf"].feature_importances_
    agg = {f: 0.0 for f in FEATURES}
    for n, v in zip(names, imp):
        col = n.split("__", 1)[1]
        base = next((c for c in CAT if col.startswith(c + "_")), col)
        agg[base] += float(v)
    reference = {c: X[c].mode().iloc[0] for c in CAT}
    reference.update({c: float(X[c].median()) for c in NUM})
    bundle = {
        "pipeline": pipe, "reference": reference,
        "importances": dict(sorted(agg.items(), key=lambda kv: -kv[1])),
        "metrics": {"accuracy": round(float(accuracy_score(y, oof >= MEDIUM_MAX)), 3),
                    "roc_auc": round(float(roc_auc_score(y, oof)), 3),
                    "samples": int(len(y)), "attrition_rate": round(float(y.mean()), 3)},
    }
    joblib.dump(bundle, path)
    return bundle, oof


def load(path: str):
    return joblib.load(path)


def predict(bundle, records, explain=True):
    """Predict for a list of employee dicts. Adds 'factors' (top drivers) when explain=True."""
    X = _frame(records)
    pipe = bundle["pipeline"]
    probs = pipe.predict_proba(X)[:, 1]
    out = []
    for i, p in enumerate(probs):
        p = float(p)
        item = {"probability": round(p * 100, 1),
                "prediction": "Likely to Leave" if p >= MEDIUM_MAX else "Likely to Stay",
                "risk_level": risk_level(p)}
        if explain:
            row = X.iloc[[i]]
            variants = []
            for f in FEATURES:
                v = row.copy()
                v[f] = bundle["reference"][f]
                variants.append(v)
            base = pipe.predict_proba(pd.concat(variants))[:, 1]
            factors = []
            for f, b in zip(FEATURES, base):
                delta = p - float(b)  # >0 pushes toward leaving vs a typical employee
                val = row.iloc[0][f]
                factors.append({"feature": LABELS[f], "value": val if isinstance(val, str) else float(val),
                                "impact": round(delta * 100, 1),
                                "direction": "increases risk" if delta > 0 else "decreases risk"})
            factors.sort(key=lambda d: -abs(d["impact"]))
            item["factors"] = [d for d in factors if abs(d["impact"]) >= 0.5][:5]
        out.append(item)
    return out
