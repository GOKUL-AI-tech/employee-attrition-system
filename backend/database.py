import os, sqlite3, sys
from flask import g, current_app
from werkzeug.security import generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "database.db")
sys.path.insert(0, os.path.dirname(BASE))

EMP_COLS = ["employee_id", "name", "age", "gender", "department", "job_role", "monthly_income",
            "years_at_company", "job_satisfaction", "work_life_balance", "overtime", "job_level",
            "performance_rating", "distance_from_home", "num_companies_worked",
            "training_times_last_year", "attrition"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL, full_name TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS employees (
  id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  age INTEGER, gender TEXT, department TEXT, job_role TEXT, monthly_income REAL,
  years_at_company REAL, job_satisfaction INTEGER, work_life_balance INTEGER, overtime TEXT,
  job_level INTEGER, performance_rating INTEGER, distance_from_home REAL,
  num_companies_worked INTEGER, training_times_last_year INTEGER,
  attrition TEXT DEFAULT 'No', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_ref INTEGER REFERENCES employees(id) ON DELETE CASCADE,
  input_json TEXT, probability REAL, prediction TEXT, risk_level TEXT, factors TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_pred_emp ON predictions(employee_ref);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_=None):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    """Create tables, default admin user and sample data (only when empty)."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    if not db.execute("SELECT 1 FROM users").fetchone():
        db.execute("INSERT INTO users(username,password_hash,full_name) VALUES(?,?,?)",
                   ("admin", generate_password_hash("admin123"), "HR Admin"))
    if not db.execute("SELECT 1 FROM employees").fetchone():
        from ml.generate_data import generate
        ph = ",".join("?" * len(EMP_COLS))
        db.executemany(f"INSERT INTO employees({','.join(EMP_COLS)}) VALUES({ph})",
                       [[r[c] for c in EMP_COLS] for r in generate()])
    db.commit()
    db.close()
