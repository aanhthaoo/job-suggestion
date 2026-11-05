import os

from fastapi import APIRouter, Depends

from ..db import connect, RealDictCursor
from ..security import require_role

router = APIRouter(prefix="/api/v1", tags=["admin"])


@router.get("/admin/stats")
def admin_stats(user: dict = Depends(require_role("admin"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        counts = {}
        for t in ("company", "users", "job_posting", "skill", "candidate", "application", "cv_document",
                  "matching_result", "cv_suggestion"):
            cur.execute(f"SELECT COUNT(*) n FROM {t}")  # noqa: S608 fixed names
            counts[t] = cur.fetchone()["n"]
        cur.execute("SELECT source, COUNT(*) n FROM job_posting GROUP BY source")
        sources = {r["source"]: r["n"] for r in cur.fetchall()}
        cur.execute("SELECT is_simulated, COUNT(*) n FROM application GROUP BY is_simulated")
        apps = {("simulated" if r["is_simulated"] else "real"): r["n"] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FILTER (WHERE is_simulated) sim, COUNT(*) FILTER (WHERE NOT is_simulated) real FROM candidate")
        cands = cur.fetchone()
        return {"postgres_status": "connected", "seed_mode": os.getenv("SEED_MODE", "full"), "counts": counts,
                "job_sources": sources, "applications_by_origin": apps, "candidates_by_origin": cands,
                "note": "posted_at, company and all candidate/application data are simulated; job text, skills and salary are real (VietJobs)"}
    finally:
        conn.close()


@router.get("/market/stats")
def market_stats():
    """Aggregates for the in-app BI page (same views Superset charts read)."""
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""SELECT skill, n_candidates, n_jobs, scarcity_index FROM v_skill_supply_demand
                       ORDER BY n_candidates DESC, n_jobs DESC LIMIT 15""")
        supply = cur.fetchall()
        cur.execute("""SELECT category, ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2)::numeric, 1) p50,
                       COUNT(*) n FROM job_posting WHERE salary_min > 0 GROUP BY category ORDER BY p50 DESC""")
        salary_by_cat = cur.fetchall()
        cur.execute("""SELECT level, ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2)::numeric, 1) p50,
                       COUNT(*) n FROM job_posting WHERE salary_min > 0 GROUP BY level""")
        salary_by_level = cur.fetchall()
        cur.execute("""SELECT source, applied, screening, interview, offer FROM v_funnel WHERE is_simulated""")
        funnel = cur.fetchall()
        cur.execute("SELECT * FROM v_match_vs_outcome ORDER BY score_band DESC")
        calibration = cur.fetchall()
        return {"skill_supply_demand": supply, "salary_by_category": salary_by_cat,
                "salary_by_level": salary_by_level, "funnel_simulated": funnel, "match_vs_outcome_simulated": calibration}
    finally:
        conn.close()
