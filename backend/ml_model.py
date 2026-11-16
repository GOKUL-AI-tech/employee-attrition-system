"""Random Forest attrition model: dataset, training, prediction and simple explanations."""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from database import BASE_DIR
from models import CATEGORICAL_FEATURES, FEATURES, LABELS, NUMERIC_FEATURES

DATASET_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "attrition_model.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "model_metrics.json")

# ---- Risk thresholds (percent). Change here or via environment variables. ----
LOW_RISK_MAX = int(os.getenv("LOW_RISK_MAX", 30))        # 0-30   -> Low
MEDIUM_RISK_MAX = int(os.getenv("MEDIUM_RISK_MAX", 60))  # 31-60  -> Medium, above -> High

RISK_TO_PREDICTION = {
    "Low": "Likely to Stay",
    "Medium": "Possible Risk of Leaving",
    "High": "Likely to Leave",
}

_state = {"pipeline": None, "meta": None}


def classify_risk(probability_percent):
    if probability_percent <= LOW_RISK_MAX:
        return "Low"
    if probability_percent <= MEDIUM_RISK_MAX:
        return "Medium"
    return "High"


# ------------------------------------------------------------------ dataset
def generate_dataset(n=1500, seed=42):
    """Create a realistic *synthetic* demo dataset (used only if dataset.csv is missing)."""
    rng = np.random.default_rng(seed)
    role_by_dept = {
        "Sales": ["Sales Executive", "Sales Representative", "Manager"],
        "Research & Development": ["Research Scientist", "Laboratory Technician", "Manager"],
        "Human Resources": ["HR Executive", "HR Manager"],
        "Finance": ["Financial Analyst", "Accountant"],
        "IT": ["Software Engineer", "Data Analyst", "Manager"],
    }
    dept = rng.choice(list(role_by_dept), n, p=[0.28, 0.32, 0.08, 0.12, 0.20])
    role = np.array([rng.choice(role_by_dept[d]) for d in dept])
    age = np.clip(rng.normal(37, 9, n), 20, 60).round().astype(int)
    total_years = np.clip(((age - 20) * rng.uniform(0.4, 1.0, n)).round(), 0, 40).astype(int)
    years = np.minimum(total_years, (total_years * rng.beta(1.5, 3, n)).round()).astype(int)
    level = np.clip(1 + total_years // 8 + rng.integers(0, 2, n), 1, 5)
    income = (level * 2600 + rng.normal(1800, 900, n)).clip(1200, 20000)
    income = (np.round(income / 10) * 10).astype(int)
    js = rng.choice([1, 2, 3, 4], n, p=[0.15, 0.22, 0.33, 0.30])
    wlb = rng.choice([1, 2, 3, 4], n, p=[0.06, 0.22, 0.52, 0.20])
    overtime = rng.choice(["Yes", "No"], n, p=[0.28, 0.72])
    dist = np.clip(rng.gamma(2.0, 5.5, n), 1, 60).round().astype(int)
    perf = rng.choice([1, 2, 3, 4], n, p=[0.02, 0.08, 0.70, 0.20])
    ncomp = np.clip(rng.poisson(2.2, n), 0, 9)
    training = np.clip(rng.poisson(2.6, n), 0, 6)
    marital = rng.choice(["Single", "Married", "Divorced"], n, p=[0.32, 0.46, 0.22])
    travel = rng.choice(["Non-Travel", "Travel_Rarely", "Travel_Frequently"], n, p=[0.12, 0.70, 0.18])
    gender = rng.choice(["Male", "Female", "Other"], n, p=[0.55, 0.43, 0.02])

    z = (-1.75
         + 1.25 * (overtime == "Yes")
         - 0.60 * (js - 2.5)
         - 0.50 * (wlb - 2.5)
         - 0.13 * np.minimum(years, 10)
         + 0.035 * dist
         - 0.00025 * (income - 6000).clip(-4000, 8000)
         + np.select([travel == "Travel_Frequently", travel == "Travel_Rarely"], [0.8, 0.2], 0.0)
         + np.select([marital == "Single", marital == "Divorced"], [0.6, 0.1], 0.0)
         + 0.12 * ncomp
         - 0.025 * (age - 37)
         - 0.08 * training
         + rng.normal(0, 0.4, n))
    attrition = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)

    return pd.DataFrame({
        "age": age, "gender": gender, "department": dept, "job_role": role,
        "monthly_income": income, "years_at_company": years, "job_satisfaction": js,
        "work_life_balance": wlb, "overtime": overtime, "distance_from_home": dist,
        "job_level": level, "performance_rating": perf, "num_companies_worked": ncomp,
        "total_working_years": total_years, "training_times": training,
        "marital_status": marital, "business_travel": travel,
        "attrition": np.where(attrition == 1, "Yes", "No"),
    })


def load_dataset():
    if not os.path.exists(DATASET_PATH):
        generate_dataset().to_csv(DATASET_PATH, index=False)
    return pd.read_csv(DATASET_PATH)


# ----------------------------------------------------------------- training
def build_pipeline():
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    forest = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1,
    )
    return Pipeline([("prep", pre), ("model", forest)])


def train_model():
    """Train on 80% of the data, evaluate on the held-out 20%, save model + metrics."""
    df = load_dataset()
    X, y = df[FEATURES], (df["attrition"] == "Yes").astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    pipe = build_pipeline().fit(X_train, y_train)
    pred = pipe.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()

    # Feature importance: permutation importance on the held-out test set, computed per
    # original feature (drop in F1 when that column is shuffled). Normalised to sum to 1.
    perm = permutation_importance(pipe, X_test, y_test, scoring="f1", n_repeats=10,
                                  random_state=42, n_jobs=-1)
    raw = np.clip(perm.importances_mean, 0, None)
    total = raw.sum() or 1.0
    importance = sorted(
        [{"feature": f, "label": LABELS[f], "importance": round(float(v / total), 4)}
         for f, v in zip(X_test.columns, raw)],
        key=lambda d: d["importance"], reverse=True)

    baseline = {}
    for f in NUMERIC_FEATURES:
        baseline[f] = float(X_train[f].median())
    for f in CATEGORICAL_FEATURES:
        baseline[f] = X_train[f].mode().iloc[0]

    meta = {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "feature_importance": importance,
        "baseline": baseline,
        "dataset": {
            "rows": int(len(df)), "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
            "attrition_rate": round(float(y.mean()), 4),
            "source": "dataset.csv (synthetic demo data unless you replace it)",
        },
        "algorithm": "Random Forest (200 trees, max depth 8) in a Scikit-learn Pipeline",
    }
    joblib.dump(pipe, MODEL_PATH)
    with open(METRICS_PATH, "w") as fh:
        json.dump(meta, fh, indent=2)
    _state["pipeline"], _state["meta"] = pipe, meta
    return meta


def ensure_model():
    """Load the saved model, or train one if none exists yet."""
    if _state["pipeline"] is None:
        if os.path.exists(MODEL_PATH) and os.path.exists(METRICS_PATH):
            _state["pipeline"] = joblib.load(MODEL_PATH)
            with open(METRICS_PATH) as fh:
                _state["meta"] = json.load(fh)
        else:
            train_model()
    return _state["pipeline"], _state["meta"]


def get_metrics():
    meta = ensure_model()[1]
    return {k: v for k, v in meta.items() if k != "baseline"}


# --------------------------------------------------------------- prediction
def _frame(rows):
    return pd.DataFrame(rows)[FEATURES]


def predict_probability(features):
    pipe, _ = ensure_model()
    return float(pipe.predict_proba(_frame([features]))[0][1])


def predict_many(list_of_features):
    if not list_of_features:
        return []
    pipe, _ = ensure_model()
    return [float(p) for p in pipe.predict_proba(_frame(list_of_features))[:, 1]]


def _risk_text(feature, value, base, increasing):
    """Plain-language sentence for one factor. Wording stays cautious (association, not proof)."""
    v = value
    if increasing:
        if feature == "overtime":
            return "Regular overtime is associated with increased predicted attrition risk."
        if feature == "job_satisfaction":
            return f"Job satisfaction is relatively low ({v}/4)."
        if feature == "work_life_balance":
            return f"Work-life balance rating is relatively low ({v}/4)."
        if feature == "years_at_company" and v < base:
            return f"Employee has limited tenure at the company ({v} yr)."
        if feature == "distance_from_home" and v > base:
            return f"Long distance from home ({v} km)."
        if feature == "monthly_income" and v < base:
            return f"Monthly income is lower than typical ({v:,})."
        if feature == "business_travel":
            return f"Business travel pattern ({v.replace('_', ' ').lower()}) is linked to higher risk."
        if feature == "marital_status":
            return f"Marital status ({v}) is linked to higher attrition in the training data."
        if feature == "num_companies_worked" and v > base:
            return f"Has worked at several companies before ({v})."
        if feature == "age" and v < base:
            return f"Younger employees show higher attrition in the training data (age {v})."
        return f"{LABELS[feature]} ({v}) is associated with higher predicted risk."
    if feature == "overtime":
        return "No regular overtime helps lower the predicted risk."
    if feature == "job_satisfaction":
        return f"Job satisfaction is good ({v}/4)."
    if feature == "work_life_balance":
        return f"Work-life balance rating is good ({v}/4)."
    if feature == "years_at_company":
        return f"Longer tenure at the company ({v} yr) lowers the predicted risk."
    return f"{LABELS[feature]} ({v}) is associated with lower predicted risk."


def explain(features, probability, top_n=5):
    """Perturbation explanation: swap one feature for the typical value and see how the
    probability changes. Bigger drop = that feature pushes the risk up for this employee."""
    _, meta = ensure_model()
    base = meta["baseline"]
    variants = []
    for f in FEATURES:
        alt = dict(features)
        alt[f] = base[f]
        variants.append(alt)
    alt_probs = predict_many(variants)

    up, down = [], []
    for f, p_alt in zip(FEATURES, alt_probs):
        if f == "gender":   # never present gender as a driver of someone's risk
            continue
        delta = probability - p_alt
        if delta >= 0.015:
            up.append((delta, f))
        elif delta <= -0.015:
            down.append((delta, f))
    up.sort(reverse=True)
    down.sort()

    def item(delta, f, inc):
        return {"feature": f, "label": LABELS[f], "impact": round(abs(delta) * 100, 1),
                "text": _risk_text(f, features[f], base[f], inc)}

    return {
        "risk_factors": [item(d, f, True) for d, f in up[:top_n]],
        "protective_factors": [item(d, f, False) for d, f in down[:3]],
    }


def predict(features, with_explanation=True):
    prob = predict_probability(features)
    percent = int(round(prob * 100))
    risk = classify_risk(percent)
    result = {
        "probability": percent,
        "risk_level": risk,
        "prediction": RISK_TO_PREDICTION[risk],
        "disclaimer": "This is a statistical prediction, not a certainty.",
    }
    if with_explanation:
        result.update(explain(features, prob))
    return result


def settings():
    return {"low_risk_max": LOW_RISK_MAX, "medium_risk_max": MEDIUM_RISK_MAX}
