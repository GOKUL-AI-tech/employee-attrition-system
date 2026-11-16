"""Generates a realistic synthetic employee dataset (used to seed the database)."""
import numpy as np

DEPT_ROLES = {
    "Sales": ["Sales Executive", "Sales Manager", "Account Representative"],
    "Engineering": ["Software Engineer", "QA Engineer", "Data Scientist", "Engineering Manager"],
    "Human Resources": ["HR Specialist", "Recruiter", "HR Manager"],
    "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
    "Marketing": ["Marketing Specialist", "Content Strategist", "Marketing Manager"],
    "Operations": ["Operations Analyst", "Logistics Coordinator", "Operations Manager"],
}
FIRST = ["Aarav", "Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Arjun", "Divya", "Karthik", "Meera",
         "John", "Emily", "Michael", "Sarah", "David", "Olivia", "Daniel", "Sophia", "James", "Emma",
         "Rohan", "Kavya", "Suresh", "Lakshmi", "Ravi", "Nisha", "Aditya", "Pooja", "Manoj", "Swathi"]
LAST = ["Kumar", "Sharma", "Patel", "Nair", "Reddy", "Iyer", "Singh", "Menon", "Gupta", "Das",
        "Smith", "Johnson", "Brown", "Miller", "Wilson", "Taylor", "Clark", "Lewis", "Walker", "Hall"]


def generate(n=600, seed=42):
    rng = np.random.default_rng(seed)
    depts = list(DEPT_ROLES)
    rows = []
    for i in range(n):
        dept = rng.choice(depts, p=[.22, .28, .07, .14, .15, .14])
        role = str(rng.choice(DEPT_ROLES[dept]))
        age = int(np.clip(rng.normal(37, 9), 20, 60))
        level = int(np.clip(round((age - 20) / 10 + rng.normal(0, .8)), 1, 5))
        income = int(np.clip(2000 + level * 2600 + rng.normal(0, 1200), 1500, 20000) // 10 * 10)
        years = int(np.clip(rng.gamma(2.2, 3) * (age - 18) / 30, 0, age - 18, ))
        sat = int(rng.choice([1, 2, 3, 4], p=[.15, .2, .35, .3]))
        wlb = int(rng.choice([1, 2, 3, 4], p=[.1, .25, .48, .17]))
        ot = "Yes" if rng.random() < .3 else "No"
        perf = int(rng.choice([1, 2, 3, 4], p=[.03, .07, .7, .2]))
        dist = int(np.clip(rng.gamma(2, 4), 1, 30))
        comps = int(np.clip(rng.poisson(2.2), 0, 9))
        train = int(np.clip(rng.poisson(2.8), 0, 6))
        z = (-3.7 + 1.4 * (ot == "Yes") + 0.55 * (3 - sat) + 0.4 * (3 - wlb)
             - 0.00028 * (income - 7000) - 0.07 * (years - 5) - 0.04 * (age - 37)
             + 0.03 * dist + 0.12 * comps - 0.2 * (level - 3) - 0.1 * (train - 3)
             + 0.4 * (dept == "Sales") + rng.normal(0, .5))
        left = rng.random() < 1 / (1 + np.exp(-z))
        rows.append({
            "employee_id": f"E{1001 + i}",
            "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "age": age, "gender": str(rng.choice(["Male", "Female"], p=[.55, .45])),
            "department": str(dept), "job_role": role, "monthly_income": income,
            "years_at_company": years, "job_satisfaction": sat, "work_life_balance": wlb,
            "overtime": ot, "job_level": level, "performance_rating": perf,
            "distance_from_home": dist, "num_companies_worked": comps,
            "training_times_last_year": train, "attrition": "Yes" if left else "No",
        })
    return rows
