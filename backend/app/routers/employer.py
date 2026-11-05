import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import connect, RealDictCursor
from ..security import require_role
from ml.matching import get_engine, invalidate, load_profile

router = APIRouter(prefix="/api/v1/employer", tags=["employer"])
employer = require_role("employer")


class JobIn(BaseModel):
    title: str
    category: str
    location: str
    level: str = "Junior"
    exp_years_min: float = 0
    education: str = "Không yêu cầu"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    description: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    contract_type: Optional[str] = "Toàn thời gian"
    working_hours: Optional[str] = None
    soft_skills: List[str] = []
    languages_required: Optional[str] = None
    skills: List[str] = []


@router.get("/jobs")
def my_jobs(user: dict = Depends(employer)):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""SELECT j.id, j.title, j.category, j.location, j.level, j.status, j.posted_at, j.salary_min,
                       j.salary_max, j.contract_type, j.working_hours, COUNT(a.id) AS n_applications
                       FROM job_posting j LEFT JOIN application a ON a.job_id=j.id
                       WHERE j.company_id=%s GROUP BY j.id ORDER BY j.posted_at DESC NULLS LAST""",
                    (user["company_id"],))
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/jobs")
def create_job(body: JobIn, user: dict = Depends(employer)):
    if body.salary_min and body.salary_max and body.salary_min > body.salary_max:
        raise HTTPException(400, "salary_min must be <= salary_max")
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""INSERT INTO job_posting (job_key, company_id, title, category, location, level, exp_years_min,
                       education, salary_min, salary_max, description, requirements,
                       benefits, contract_type, working_hours, soft_skills, languages_required,
                       source, posted_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'employer', now()) RETURNING id""",
                    (f"emp-{uuid.uuid4().hex[:12]}", user["company_id"], body.title, body.category, body.location,
                     body.level, body.exp_years_min, body.education, body.salary_min, body.salary_max,
                     body.description, body.requirements,
                     body.benefits, body.contract_type, body.working_hours, body.soft_skills, body.languages_required))
        jid = cur.fetchone()["id"]
        cur.execute("""INSERT INTO job_skill (job_id, skill_id, weight)
                       SELECT %s, id, 1.0 FROM skill WHERE lower(name) = ANY(%s)""",
                    (jid, [s.lower() for s in body.skills]))
        conn.commit()
        invalidate()  # engine rebuilds (cheap transform) so the new job becomes matchable
        return {"id": jid}
    finally:
        conn.close()


def _own_job(cur, job_id: int, user: dict):
    cur.execute("SELECT id, title FROM job_posting WHERE id=%s AND company_id=%s", (job_id, user["company_id"]))
    j = cur.fetchone()
    if not j:
        raise HTTPException(404, "Job not found")
    return j


@router.get("/jobs/{job_id}/candidates")
def ranked_candidates(job_id: int, missing_skill: Optional[str] = None, user: dict = Depends(employer)):
    """Applicants ranked by match score; `missing_skill` keeps only those lacking that skill."""
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        job = _own_job(cur, job_id, user)
        cur.execute("""SELECT a.id AS application_id, a.candidate_id, a.status, a.applied_at, c.full_name,
                       c.exp_years, c.education, c.location FROM application a
                       JOIN candidate c ON c.id=a.candidate_id WHERE a.job_id=%s""", (job_id,))
        apps = cur.fetchall()
        eng = get_engine()
        out = []
        for a in apps:
            ex = eng.explain(load_profile(cur, a["candidate_id"]), job_id)
            if missing_skill and missing_skill.lower() not in [m.lower() for m in ex["missing_skills"]]:
                continue
            out.append({**a, "score": ex["score"], "level": ex["level"], "matched_skills": ex["matched_skills"],
                        "missing_skills": ex["missing_skills"], "explanation": ex["explanation"]})
        out.sort(key=lambda r: -r["score"])
        return {"job": job, "candidates": out}
    finally:
        conn.close()


@router.get("/kpi")
def kpi(user: dict = Depends(employer)):
    """Every query is scoped by the company_id inside the token."""
    cid = user["company_id"]
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) n FROM job_posting WHERE company_id=%s AND status='active'", (cid,))
        n_jobs = cur.fetchone()["n"]
        cur.execute("""SELECT COUNT(*) AS applied,
                       COUNT(*) FILTER (WHERE a.stage_reached>=1) AS screening,
                       COUNT(*) FILTER (WHERE a.stage_reached>=2) AS interview,
                       COUNT(*) FILTER (WHERE a.stage_reached>=3) AS offer,
                       ROUND(AVG(a.match_score)::numeric, 3) AS avg_match,
                       ROUND(AVG(EXTRACT(EPOCH FROM (a.updated_at - a.applied_at))/86400)::numeric, 1) AS avg_days_to_response
                       FROM application a JOIN job_posting j ON j.id=a.job_id WHERE j.company_id=%s""", (cid,))
        funnel = cur.fetchone()
        cur.execute("""SELECT s.name AS skill, COUNT(*) AS n_missing
                       FROM application a JOIN job_posting j ON j.id=a.job_id
                       JOIN job_skill js ON js.job_id=j.id JOIN skill s ON s.id=js.skill_id
                       LEFT JOIN candidate_skill cs ON cs.candidate_id=a.candidate_id AND cs.skill_id=js.skill_id
                       WHERE j.company_id=%s AND cs.skill_id IS NULL
                       GROUP BY s.name ORDER BY n_missing DESC, s.name LIMIT 8""", (cid,))
        top_missing = cur.fetchall()
        cur.execute("SELECT name FROM company WHERE id=%s", (cid,))
        comp = cur.fetchone()
        return {"company": comp["name"] if comp else None, "company_id": cid, "n_active_jobs": n_jobs,
                "funnel": funnel, "top_missing_skills": top_missing}
    finally:
        conn.close()
