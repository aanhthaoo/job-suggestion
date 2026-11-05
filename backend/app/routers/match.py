import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..db import connect, RealDictCursor
from ..security import require_role
from .cv import candidate_id
from .jobs import SELECT
from ml import train_salary
from ml.cv_suggest import suggest
from ml.matching import band, get_engine, load_profile, refresh_matches

router = APIRouter(prefix="/api/v1", tags=["match"])


@router.get("/recommendations")
def recommendations(k: int = 20, user: dict = Depends(require_role("candidate"))):
    k = max(1, min(k, 100))
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cid = candidate_id(cur, user)
        version = get_engine().default_model
        cur.execute("SELECT 1 FROM matching_result WHERE candidate_id=%s AND model_version=%s LIMIT 1", (cid, version))
        if not cur.fetchone():
            refresh_matches(conn, cid)
        cur.execute("""SELECT job_id, score, components_json, matched_skills, missing_skills
                       FROM matching_result WHERE candidate_id=%s AND model_version=%s
                       ORDER BY score DESC LIMIT %s""", (cid, version, k))
        items = []
        for m in cur.fetchall():
            cur.execute(SELECT + " WHERE j.id=%s", (m["job_id"],))
            job = cur.fetchone()
            if not job:
                continue
            s = float(m["score"])
            matched, missing = m["matched_skills"] or [], m["missing_skills"] or []
            reason = f"Khớp {len(matched)}/{len(matched) + len(missing)} kỹ năng" + (
                f"; thiếu {', '.join(missing[:3])}" if missing else "")
            items.append({"job": job, "score": s, "level": band(s), "components": m["components_json"],
                          "matched_skills": matched, "missing_skills": missing, "reason": reason})
        return {"model_version": version, "recommendations": items}
    finally:
        conn.close()


@router.get("/jobs/{job_id}/match")
def job_match(job_id: int, user: dict = Depends(require_role("candidate"))):
    eng = get_engine()
    if job_id not in eng.job_pos:
        raise HTTPException(404, "Job not found")
    conn = connect(retries=3)
    try:
        cur = conn.cursor()
        return eng.explain(load_profile(cur, candidate_id(cur, user)), job_id)
    finally:
        conn.close()


@router.post("/cv/suggest")
def cv_suggest(job_id: int, user: dict = Depends(require_role("candidate"))):
    eng = get_engine()
    if job_id not in eng.job_pos:
        raise HTTPException(404, "Job not found")
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cid = candidate_id(cur, user)
        cur.execute("SELECT id, raw_text, health_issues_json FROM cv_document WHERE candidate_id=%s "
                    "ORDER BY id DESC LIMIT 1", (cid,))
        cv = cur.fetchone()
        if not cv:
            raise HTTPException(400, "Hãy tải CV lên trước khi xin gợi ý")
        cur.execute("SELECT content_json, source FROM cv_suggestion WHERE cv_id=%s AND job_id=%s", (cv["id"], job_id))
        cached = cur.fetchone()
        if cached:
            return {"content": cached["content_json"], "source": cached["source"], "cached": True}
        cur.execute(SELECT + " WHERE j.id=%s", (job_id,))
        job = cur.fetchone()
        ex = eng.explain(load_profile(cur, cid), job_id)
        res = suggest(job, cv["raw_text"] or "", ex["missing_skills"], ex["matched_skills"],
                      (cv["health_issues_json"] or {}).get("issues", []))
        cur.execute("""INSERT INTO cv_suggestion (cv_id, job_id, content_json, source) VALUES (%s,%s,%s,%s)
                       ON CONFLICT (cv_id, job_id) DO UPDATE SET content_json=EXCLUDED.content_json,
                       source=EXCLUDED.source, created_at=now()""",
                    (cv["id"], job_id, json.dumps(res["content"]), res["source"]))
        conn.commit()
        return {**res, "cached": False}
    finally:
        conn.close()


def _round(v):
    return None if v is None else round(float(v), 1)


@router.get("/salary/estimate")
def salary_estimate(job_id: Optional[int] = None, category: Optional[str] = None, level: Optional[str] = None,
                    location: Optional[str] = None, exp_years: float = 0):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        edu, n_sk = "Đại học", 3
        if job_id:
            cur.execute("""SELECT category, level, location, exp_years_min, education,
                           (SELECT COUNT(*) FROM job_skill WHERE job_id=j.id) n FROM job_posting j WHERE id=%s""",
                        (job_id,))
            j = cur.fetchone()
            if not j:
                raise HTTPException(404, "Job not found")
            category, level, location = j["category"], j["level"], j["location"]
            exp_years, edu, n_sk = float(j["exp_years_min"] or 0), j["education"], j["n"]
        if not category:
            raise HTTPException(400, "job_id or category required")
        base = ("SELECT COUNT(*) n, percentile_cont(0.25) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2) p25, "
                "percentile_cont(0.5) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2) p50, "
                "percentile_cont(0.75) WITHIN GROUP (ORDER BY (salary_min+salary_max)/2) p75 "
                "FROM job_posting WHERE salary_min > 0 AND category=%s")
        cur.execute(base + (" AND level=%s" if level else ""), [category] + ([level] if level else []))
        seg = cur.fetchone()
        if seg["n"] < 5 and level:  # segment too thin: widen to the whole category
            cur.execute(base, [category])
            seg = cur.fetchone()
        pred = train_salary.predict_salary(category, level or "Junior", location or "Hà Nội", exp_years, edu, n_sk)
        mfile = train_salary.MODELS / "salary_metrics.json"
        beats = bool(mfile.exists() and json.loads(mfile.read_text(encoding="utf-8")).get("use_model"))
        return {"unit": "triệu VND/tháng",
                "segment": {"n": seg["n"], "p25": _round(seg["p25"]), "p50": _round(seg["p50"]),
                            "p75": _round(seg["p75"])},
                "model_prediction": pred, "model_beats_baseline": beats,
                "estimate": pred if beats and pred is not None else _round(seg["p50"])}
    finally:
        conn.close()
