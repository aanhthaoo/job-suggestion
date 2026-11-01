"""Seed PostgreSQL with demo data for the BI dashboard.

Idempotent: safe to run on every backend start (uses ON CONFLICT DO NOTHING).
Creates: companies, jobs, job_skills, users, applications.
"""
import os
import json
import random
from datetime import datetime, timedelta, timezone

from .db import connect

_HERE = os.path.dirname(__file__)
_JOBS_CANDIDATES = [
    os.environ.get("MOCK_JOBS_FILE"),
    os.path.join(_HERE, "..", "..", "frontend", "mock", "jobs.json"),
    "/app/frontend/mock/jobs.json",
]


def _load_jobs():
    path = next((p for p in _JOBS_CANDIDATES if p and os.path.exists(p)), None)
    if path is None:
        raise RuntimeError("jobs.json not found in any candidate path")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company_id TEXT REFERENCES companies(id),
    company_name TEXT,
    description TEXT,
    requirements TEXT,
    location TEXT,
    salary_min BIGINT,
    salary_max BIGINT,
    currency TEXT,
    experience_years INT,
    job_type TEXT,
    work_mode TEXT,
    status TEXT,
    posted_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill)
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    full_name TEXT,
    role TEXT,
    created_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    status TEXT,
    applied_at TIMESTAMPTZ
);
"""

DEMO_USERS = [
    ("u_user", "user@test.com", "Nguyễn Văn User", "candidate"),
    ("u_hr", "hr@test.com", "Trần Thị HR", "hr"),
    ("u_admin", "admin@test.com", "Lê Admin", "admin"),
]

CANDIDATE_NAMES = [
    "Phạm Minh Anh", "Hoàng Văn Bình", "Đỗ Thị Châu", "Vũ Quốc Đạt",
    "Bùi Thu Hà", "Đặng Văn Hiếu", "Phan Ngọc Huyền", "Trần Tuấn Kiệt",
    "Lê Thị Lan", "Nguyễn Hải Long", "Hoàng Thu Mai", "Võ Văn Nam",
    "Đinh Thị Oanh", "Trương Minh Phúc", "Ngô Thị Quỳnh",
]

STATUS_WEIGHTS = [
    ("submitted", 40),
    ("reviewed", 25),
    ("interviewing", 15),
    ("accepted", 10),
    ("rejected", 10),
]


def seed():
    jobs = _load_jobs()
    conn = connect()
    cur = conn.cursor()
    cur.execute(SCHEMA)

    # Companies
    companies = {}
    for j in jobs:
        companies[str(j["company_id"])] = j.get("company_name") or f"Company {j['company_id']}"
    for cid, name in companies.items():
        cur.execute(
            "INSERT INTO companies (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (cid, name),
        )

    # Jobs
    for j in jobs:
        cur.execute(
            """INSERT INTO jobs (id, title, company_id, company_name, description, requirements,
                   location, salary_min, salary_max, currency, experience_years,
                   job_type, work_mode, status, posted_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (id) DO UPDATE SET
                   title=EXCLUDED.title, company_id=EXCLUDED.company_id,
                   company_name=EXCLUDED.company_name, location=EXCLUDED.location,
                   salary_min=EXCLUDED.salary_min, salary_max=EXCLUDED.salary_max,
                   currency=EXCLUDED.currency, experience_years=EXCLUDED.experience_years,
                   job_type=EXCLUDED.job_type, work_mode=EXCLUDED.work_mode,
                   status=EXCLUDED.status, posted_at=EXCLUDED.posted_at""",
            (
                str(j["id"]), j["title"], str(j["company_id"]), j.get("company_name"),
                j.get("description"), j.get("requirements"), j.get("location"),
                j.get("salary_min"), j.get("salary_max"), j.get("currency", "VND"),
                j.get("experience_years", 0), j.get("job_type"), j.get("work_mode"),
                j.get("status", "active"), j.get("posted_at"),
            ),
        )

    # Job skills (refreshed each run)
    cur.execute("DELETE FROM job_skills")
    for j in jobs:
        for skill in j.get("skills_required", []):
            cur.execute(
                "INSERT INTO job_skills (job_id, skill) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (str(j["id"]), skill),
            )

    # Users: demo accounts + synthetic candidates
    now = datetime.now(timezone.utc)
    all_users = list(DEMO_USERS)
    for i, name in enumerate(CANDIDATE_NAMES, start=1):
        all_users.append((f"c{i}", f"candidate{i}@example.com", name, "candidate"))
    for uid, email, full_name, role in all_users:
        cur.execute(
            """INSERT INTO users (id, email, full_name, role, created_at)
               VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
            (uid, email, full_name, role, now.isoformat()),
        )

    # Applications: deterministic synthetic set over the last 75 days
    cur.execute("SELECT COUNT(*) FROM applications")
    existing = cur.fetchone()[0]
    if existing == 0:
        rng = random.Random(42)
        candidate_ids = [u[0] for u in all_users if u[3] == "candidate"]
        job_ids = [str(j["id"]) for j in jobs]
        statuses = [s for s, _ in STATUS_WEIGHTS]
        weights = [w for _, w in STATUS_WEIGHTS]
        for n in range(120):
            app_id = f"a{n+1}"
            job_id = rng.choice(job_ids)
            user_id = rng.choice(candidate_ids)
            status = rng.choices(statuses, weights=weights, k=1)[0]
            days_ago = rng.randint(0, 74)
            applied = (now - timedelta(days=days_ago, hours=rng.randint(0, 23))).isoformat()
            cur.execute(
                """INSERT INTO applications (id, job_id, user_id, status, applied_at)
                   VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
                (app_id, job_id, user_id, status, applied),
            )

    conn.commit()

    def count(table):
        cur.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 - fixed table names
        return cur.fetchone()[0]

    summary = {
        "companies": count("companies"),
        "jobs": count("jobs"),
        "job_skills": count("job_skills"),
        "users": count("users"),
        "applications": count("applications"),
    }
    cur.close()
    conn.close()
    return summary


if __name__ == "__main__":
    result = seed()
    print("Seeded PostgreSQL:", result)
