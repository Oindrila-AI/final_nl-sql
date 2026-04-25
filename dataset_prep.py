"""
dataset_prep.py
Sets up a sample SQLite database (company.db) with realistic tables and seed data,
then exports the schema string used during training and inference.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "company.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    dept_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS employees (
    emp_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT UNIQUE,
    salary      REAL NOT NULL,
    dept_id     INTEGER,
    hire_date   TEXT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS projects (
    project_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    budget       REAL,
    start_date   TEXT,
    end_date     TEXT
);

CREATE TABLE IF NOT EXISTS employee_projects (
    emp_id     INTEGER,
    project_id INTEGER,
    role       TEXT,
    PRIMARY KEY (emp_id, project_id),
    FOREIGN KEY (emp_id)     REFERENCES employees(emp_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
"""

SEED_DATA = {
    "departments": [
        ("Engineering",),
        ("Marketing",),
        ("Sales",),
        ("Human Resources",),
        ("Finance",),
    ],
    "employees": [
        ("Alice", "Smith", "alice@company.com", 95000, 1, "2020-03-15"),
        ("Bob", "Johnson", "bob@company.com", 88000, 1, "2019-07-22"),
        ("Carol", "Williams", "carol@company.com", 72000, 2, "2021-01-10"),
        ("David", "Brown", "david@company.com", 67000, 3, "2022-06-01"),
        ("Eve", "Davis", "eve@company.com", 105000, 1, "2018-11-30"),
        ("Frank", "Miller", "frank@company.com", 78000, 4, "2020-09-12"),
        ("Grace", "Wilson", "grace@company.com", 91000, 5, "2019-04-18"),
        ("Hank", "Moore", "hank@company.com", 62000, 3, "2023-02-28"),
        ("Ivy", "Taylor", "ivy@company.com", 84000, 2, "2021-08-05"),
        ("Jack", "Anderson", "jack@company.com", 99000, 1, "2017-12-01"),
    ],
    "projects": [
        ("Project Alpha", 500000, "2023-01-01", "2024-06-30"),
        ("Project Beta", 250000, "2023-06-15", "2024-03-31"),
        ("Project Gamma", 750000, "2022-09-01", "2025-12-31"),
        ("Marketing Blitz", 120000, "2024-01-01", "2024-12-31"),
    ],
    "employee_projects": [
        (1, 1, "Lead Engineer"),
        (2, 1, "Backend Developer"),
        (5, 3, "Architect"),
        (10, 3, "Senior Developer"),
        (3, 4, "Campaign Manager"),
        (9, 4, "Content Strategist"),
        (4, 2, "Sales Liaison"),
        (1, 3, "Consultant"),
    ],
}

SAMPLE_PAIRS = [
    {
        "question": "Show all employees",
        "sql": "SELECT * FROM employees",
    },
    {
        "question": "List all department names",
        "sql": "SELECT dept_name FROM departments",
    },
    {
        "question": "What is the average salary of employees?",
        "sql": "SELECT AVG(salary) FROM employees",
    },
    {
        "question": "Show the names of employees in the Engineering department",
        "sql": "SELECT e.first_name, e.last_name FROM employees e JOIN departments d ON e.dept_id = d.dept_id WHERE d.dept_name = 'Engineering'",
    },
    {
        "question": "How many employees are there in each department?",
        "sql": "SELECT d.dept_name, COUNT(*) FROM employees e JOIN departments d ON e.dept_id = d.dept_id GROUP BY d.dept_name",
    },
    {
        "question": "Which employee has the highest salary?",
        "sql": "SELECT first_name, last_name, salary FROM employees ORDER BY salary DESC LIMIT 1",
    },
    {
        "question": "List all projects with a budget greater than 300000",
        "sql": "SELECT * FROM projects WHERE budget > 300000",
    },
    {
        "question": "Show employees hired after 2021",
        "sql": "SELECT first_name, last_name, hire_date FROM employees WHERE hire_date > '2021-01-01'",
    },
    {
        "question": "What projects is Alice working on?",
        "sql": "SELECT p.project_name, ep.role FROM projects p JOIN employee_projects ep ON p.project_id = ep.project_id JOIN employees e ON ep.emp_id = e.emp_id WHERE e.first_name = 'Alice'",
    },
    {
        "question": "Show the total budget of all projects",
        "sql": "SELECT SUM(budget) FROM projects",
    },
]


def get_schema_string() -> str:
    """Return a compact, model-friendly representation of the database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]

    parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_defs = ", ".join(f"{c[1]} {c[2]}" for c in columns)
        parts.append(f"{table}({col_defs})")

    conn.close()
    return " | ".join(parts)


def init_db():
    """Create the database, schema, and seed data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)

    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO departments (dept_name) VALUES (?)", SEED_DATA["departments"])
        cursor.executemany(
            "INSERT INTO employees (first_name, last_name, email, salary, dept_id, hire_date) VALUES (?,?,?,?,?,?)",
            SEED_DATA["employees"],
        )
        cursor.executemany(
            "INSERT INTO projects (project_name, budget, start_date, end_date) VALUES (?,?,?,?)",
            SEED_DATA["projects"],
        )
        cursor.executemany(
            "INSERT INTO employee_projects (emp_id, project_id, role) VALUES (?,?,?)",
            SEED_DATA["employee_projects"],
        )
        conn.commit()
        print(f"Database created and seeded at {DB_PATH}")
    else:
        print(f"Database already exists at {DB_PATH}")

    conn.close()


def export_sample_pairs():
    """Export sample NL-SQL pairs to a JSON file for quick local testing."""
    out = Path(__file__).parent / "sample_pairs.json"
    with open(out, "w") as f:
        json.dump(SAMPLE_PAIRS, f, indent=2)
    print(f"Exported {len(SAMPLE_PAIRS)} sample pairs to {out}")


if __name__ == "__main__":
    init_db()
    schema = get_schema_string()
    print(f"\nSchema string for model input:\n{schema}")
    export_sample_pairs()