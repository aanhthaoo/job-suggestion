from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from ..db import connect, RealDictCursor
from ..security import optional_user

router = APIRouter(prefix="/api/v1", tags=["jobs"])

SELECT = """
SELECT j.id, j.job_key, j.title, j.category, j.location, j.level, j.exp_years_min,
       j.education, j.salary_min, j.salary_max, j.description, j.requirements,
       j.benefits, j.contract_type, j.working_hours, j.soft_skills, j.languages_required,
       j.source, j.status, j.posted_at, c.name AS company_name, j.company_id,
       COALESCE((SELECT array_agg(s.name ORDER BY js.weight DESC, s.name)
                 FROM job_skill js JOIN skill s ON s.id = js.skill_id
                 WHERE js.job_id = j.id), '{}') AS skills_required
FROM job_posting j LEFT JOIN company c ON c.id = j.company_id
"""


@router.get("/jobs")
def list_jobs(search: Optional[str] = None, category: Optional[str] = None,
              location: Optional[str] = None, level: Optional[str] = None,
              page: int = 1, limit: int = 10, user=Depends(optional_user)):
    limit = max(1, min(limit, 100))
    where, args = ["j.status='active'"], []
    if search:
        where.append("(j.title ILIKE %s OR j.description ILIKE %s OR c.name ILIKE %s OR EXISTS ("
                     "SELECT 1 FROM job_skill js JOIN skill s ON s.id=js.skill_id "
                     "WHERE js.job_id=j.id AND s.name ILIKE %s))")
        args += [f"%{search}%"] * 4
    for col, val in (("j.category", category), ("j.location", location), ("j.level", level)):
        if val:
            where.append(f"{col} ILIKE %s")
            args.append(val)
    w = " WHERE " + " AND ".join(where)
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) n FROM job_posting j LEFT JOIN company c ON c.id=j.company_id" + w, args)
        total = cur.fetchone()["n"]
        cur.execute(SELECT + w + " ORDER BY j.posted_at DESC NULLS LAST, j.id LIMIT %s OFFSET %s",
                    args + [limit, (max(page, 1) - 1) * limit])
        items = cur.fetchall()
        if user and user["role"] == "candidate":  # attach the model's score; the UI never computes it
            cur.execute("SELECT id FROM candidate WHERE user_id=%s", (user["id"],))
            c = cur.fetchone()
            if c:
                from ml.matching import band, get_engine, load_profile
                scores = get_engine().score_jobs(load_profile(conn.cursor(), c["id"]), [j["id"] for j in items])
                for j in items:
                    s = scores.get(j["id"])
                    j["match_score"] = None if s is None else round(s, 4)
                    j["match_level"] = None if s is None else band(s)
        return {"items": items, "total": total, "page": page, "limit": limit}
    finally:
        conn.close()


@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(SELECT + " WHERE j.id=%s", (job_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Job not found")
        return row
    finally:
        conn.close()
