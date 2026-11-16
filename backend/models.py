"""Employee field definitions and input validation (no ORM - plain and simple)."""

DEPARTMENTS = ["Sales", "Research & Development", "Human Resources", "Finance", "IT"]

JOB_ROLES = [
    "Sales Executive", "Sales Representative",
    "Research Scientist", "Laboratory Technician",
    "HR Executive", "HR Manager",
    "Financial Analyst", "Accountant",
    "Software Engineer", "Data Analyst", "Manager",
]

CHOICES = {
    "gender": ["Male", "Female", "Other"],
    "department": DEPARTMENTS,
    "job_role": JOB_ROLES,
    "overtime": ["Yes", "No"],
    "marital_status": ["Single", "Married", "Divorced"],
    "business_travel": ["Non-Travel", "Travel_Rarely", "Travel_Frequently"],
}

# name -> (min, max)
NUMERIC_RANGES = {
    "age": (18, 65),
    "monthly_income": (1000, 50000),
    "years_at_company": (0, 50),
    "job_satisfaction": (1, 4),
    "work_life_balance": (1, 4),
    "distance_from_home": (0, 100),
    "job_level": (1, 5),
    "performance_rating": (1, 4),
    "num_companies_worked": (0, 20),
    "total_working_years": (0, 50),
    "training_times": (0, 10),
}

NUMERIC_FEATURES = list(NUMERIC_RANGES.keys())
CATEGORICAL_FEATURES = list(CHOICES.keys())
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

LABELS = {
    "age": "Age", "monthly_income": "Monthly income", "years_at_company": "Years at company",
    "job_satisfaction": "Job satisfaction", "work_life_balance": "Work-life balance",
    "distance_from_home": "Distance from home", "job_level": "Job level",
    "performance_rating": "Performance rating", "num_companies_worked": "Companies worked",
    "total_working_years": "Total working years", "training_times": "Training times last year",
    "gender": "Gender", "department": "Department", "job_role": "Job role",
    "overtime": "Overtime", "marital_status": "Marital status", "business_travel": "Business travel",
}


def validate_employee(data, require_identity=True):
    """Return (clean_dict, errors_dict). Errors are short, HR-friendly messages."""
    clean, errors = {}, {}
    if not isinstance(data, dict):
        return {}, {"_": "Invalid request body."}

    if require_identity:
        for key, label in (("employee_id", "Employee ID"), ("name", "Name")):
            value = str(data.get(key, "") or "").strip()
            if not value:
                errors[key] = f"{label} is required."
            elif len(value) > 60:
                errors[key] = f"{label} is too long."
            else:
                clean[key] = value

    for key, (lo, hi) in NUMERIC_RANGES.items():
        raw = data.get(key)
        if raw is None or str(raw).strip() == "":
            errors[key] = f"{LABELS[key]} is required."
            continue
        try:
            num = float(raw)
        except (TypeError, ValueError):
            errors[key] = f"{LABELS[key]} must be a number."
            continue
        if not lo <= num <= hi:
            errors[key] = f"{LABELS[key]} must be between {lo} and {hi}."
            continue
        clean[key] = int(round(num))

    for key, options in CHOICES.items():
        value = data.get(key)
        if value is None or str(value).strip() == "":
            errors[key] = f"{LABELS[key]} is required."
        elif value not in options:
            errors[key] = f"{LABELS[key]} must be one of: {', '.join(options)}."
        else:
            clean[key] = value

    if ("years_at_company" in clean and "total_working_years" in clean
            and clean["years_at_company"] > clean["total_working_years"]):
        errors["years_at_company"] = "Years at company cannot exceed total working years."

    return clean, errors
