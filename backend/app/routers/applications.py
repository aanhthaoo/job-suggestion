from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import connect, RealDictCursor
from ..security import current_user, require_role
from .cv import candidate_id
from ml.matching import get_engine, load_profile

router = APIRouter(prefix="/api/v1", tags=["applications"])
STAGE = {"applied": 0, "screening": 1, "interview": 2, "offer": 3}


class ApplyIn(BaseModel):
    job_id: int
    source: Literal["recommend", "search"] = "search"


class StatusIn(BaseModel):
    status: Literal["applied", "screening", "interview", "offer", "rejected"]


@router.post("/applications")
def apply(body: ApplyIn, user: dict = Depends(require_role("candidate"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cid = candidate_id(cur, user)
        cur.execute("SELECT 1 FROM job_posting WHERE id=%s AND status='active'", (body.job_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Job not found")
        cur.execute("SELECT 1 FROM application WHERE candidate_id=%s AND job_id=%s", (cid, body.job_id))
        if cur.fetchone():
            raise HTTPException(409, "Đã ứng tuyển vị trí này")
        score = get_engine().score_jobs(load_profile(cur, cid), [body.job_id]).get(body.job_id)
        cur.execute("""INSERT INTO application (candidate_id, job_id, match_score, source)
                       VALUES (%s,%s,%s,%s) RETURNING id, status, applied_at""",
                    (cid, body.job_id, None if score is None else round(score, 4), body.source))
        row = cur.fetchone()
        conn.commit()
        return {**row, "match_score": score}
    finally:
        conn.close()


@router.get("/applications")
def my_applications(user: dict = Depends(require_role("candidate"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cid = candidate_id(cur, user)
        cur.execute("""SELECT a.id, a.job_id, a.status, a.match_score, a.source, a.applied_at, a.updated_at,
                       j.title, j.location, c.name AS company_name
                       FROM application a JOIN job_posting j ON j.id=a.job_id
                       LEFT JOIN company c ON c.id=j.company_id
                       WHERE a.candidate_id=%s ORDER BY a.applied_at DESC""", (cid,))
        return cur.fetchall()
    finally:
        conn.close()


@router.patch("/applications/{app_id}")
def update_status(app_id: int, body: StatusIn, user: dict = Depends(require_role("employer"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""SELECT a.id, a.stage_reached, j.company_id FROM application a
                       JOIN job_posting j ON j.id=a.job_id WHERE a.id=%s""", (app_id,))
        a = cur.fetchone()
        if not a or a["company_id"] != user["company_id"]:  # 404 (not 403) so other tenants' ids don't leak
            raise HTTPException(404, "Application not found")
        stage = max(a["stage_reached"], STAGE.get(body.status, 0))
        cur.execute("""UPDATE application SET status=%s, stage_reached=%s, updated_at=now() WHERE id=%s
                       RETURNING id, status, stage_reached""", (body.status, stage, app_id))
        row = cur.fetchone()
        conn.commit()
        return row
    finally:
        conn.close()
