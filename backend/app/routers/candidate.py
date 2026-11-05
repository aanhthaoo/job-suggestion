from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import connect, RealDictCursor
from ..security import require_role
from .cv import candidate_id
from ml.matching import refresh_matches

router = APIRouter(prefix="/api/v1/candidate", tags=["candidate"])


class ProfileIn(BaseModel):
    full_name: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = None
    exp_years: Optional[float] = None
    education: Optional[str] = None
    location: Optional[str] = None
    expected_salary: Optional[float] = None
    skills: Optional[List[str]] = None  # manual skills (replaces the previous manual set)


def _profile(cur, cid):
    cur.execute("""SELECT c.*, u.email FROM candidate c JOIN users u ON u.id = c.user_id WHERE c.id=%s""", (cid,))
    p = cur.fetchone()
    if not p:
        cur.execute("SELECT * FROM candidate WHERE id=%s", (cid,))
        p = cur.fetchone()
    cur.execute("""SELECT s.name, cs.source FROM candidate_skill cs JOIN skill s ON s.id=cs.skill_id
                   WHERE cs.candidate_id=%s ORDER BY s.name""", (cid,))
    p["skills"] = cur.fetchall()
    cur.execute("""SELECT id, filename, health_score, health_issues_json, parsed_json, raw_text, created_at FROM cv_document
                   WHERE candidate_id=%s ORDER BY id DESC LIMIT 1""", (cid,))
    p["latest_cv"] = cur.fetchone()
    return p


@router.get("/profile")
def get_profile(user: dict = Depends(require_role("candidate"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        return _profile(cur, candidate_id(cur, user))
    finally:
        conn.close()


@router.put("/profile")
def update_profile(body: ProfileIn, user: dict = Depends(require_role("candidate"))):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cid = candidate_id(cur, user)
        data = body.model_dump(exclude_none=True)
        skills = data.pop("skills", None)
        if data:
            sets = ", ".join(f"{k}=%s" for k in data)  # keys come from the pydantic model, never the client
            cur.execute(f"UPDATE candidate SET {sets} WHERE id=%s", list(data.values()) + [cid])  # noqa: S608
        if skills is not None:
            cur.execute("DELETE FROM candidate_skill WHERE candidate_id=%s AND source='manual'", (cid,))
            cur.execute("""INSERT INTO candidate_skill (candidate_id, skill_id, source)
                           SELECT %s, id, 'manual' FROM skill WHERE lower(name) = ANY(%s)
                           ON CONFLICT (candidate_id, skill_id) DO NOTHING""",
                        (cid, [s.lower() for s in skills]))
        conn.commit()
        refresh_matches(conn, cid)
        return _profile(cur, cid)
    finally:
        conn.close()
