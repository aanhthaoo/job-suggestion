"""Print table counts + thresholds required by checklist 1. Usage: python scripts/check_counts.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db import connect  # noqa: E402

THRESH = {"job_posting": 2000, "candidate": 300, "application": 1500}
conn = connect(retries=3)
cur = conn.cursor()
ok = True
for t in ("company", "users", "job_posting", "skill", "job_skill", "candidate", "candidate_skill",
          "cv_document", "application", "matching_result", "cv_suggestion"):
    cur.execute(f"SELECT COUNT(*) FROM {t}")  # noqa: S608
    n = cur.fetchone()[0]
    need = THRESH.get(t)
    flag = "" if need is None else (" OK" if n >= need else f" FAIL (<{need})")
    ok &= need is None or n >= need
    print(f"{t:18s}{n:7d}{flag}")
cur.execute("SELECT MIN(posted_at)::date, MAX(posted_at)::date FROM job_posting")
print("posted_at range:", cur.fetchone())
cur.execute("SELECT source, COUNT(*) FROM job_posting GROUP BY 1")
print("job sources:", cur.fetchall())
sys.exit(0 if ok else 1)
