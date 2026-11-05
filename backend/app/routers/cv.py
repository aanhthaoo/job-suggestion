import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..cv_parser import parse_cv
from ..db import connect
from ..security import require_role
from ml.cv_health import score_cv
from ml.matching import refresh_matches

router = APIRouter(prefix="/api/v1", tags=["cv"])
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED = {"pdf", "docx"}
MAX_BYTES = 5 * 1024 * 1024


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Save to a uuid-named file (never trust client filename). Returns (path, ext)."""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, "Only PDF and DOCX files are supported")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 5MB)")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.{ext}")
    with open(path, "wb") as fh:
        fh.write(content)
    return path, ext


def candidate_id(cur, user: dict) -> int:
    cur.execute("SELECT id FROM candidate WHERE user_id=%s", (user["id"],))
    r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Candidate profile not found")
    return r["id"] if isinstance(r, dict) else r[0]


@router.post("/cv/parse")
async def parse_cv_endpoint(file: UploadFile = File(...)):
    """Stateless parse (no login, nothing stored)."""
    path, ext = await save_upload(file)
    try:
        r = parse_cv(path, ext)
        text = r["text"]
        return {"skills": r["skills"], "experience_years": r["experience_years"],
                "education": r["education"], "text_preview": text[:500] + "..." if len(text) > 500 else text}
    except ValueError as e:
        raise HTTPException(422, str(e))
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...), user: dict = Depends(require_role("candidate"))):
    """Parse CV, score health, replace CV-derived skills, recompute matching."""
    path, ext = await save_upload(file)
    conn = connect(retries=3)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM skill")
        vocab = [r[0] for r in cur.fetchall()]
        try:
            parsed = parse_cv(path, ext, vocab=vocab)
        except ValueError as e:
            raise HTTPException(422, str(e))
        health = score_cv(parsed)
        cid = candidate_id(cur, user)
        public = {k: v for k, v in parsed.items() if k not in ("text", "text_nodiacritic")}
        cur.execute("""INSERT INTO cv_document (candidate_id, filename, raw_text, parsed_json, health_score,
                       health_issues_json) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (cid, (file.filename or "cv")[:200], parsed["text"], json.dumps(public),
                     health["score"], json.dumps(health)))
        cv_id = cur.fetchone()[0]
        cur.execute("DELETE FROM candidate_skill WHERE candidate_id=%s AND source='cv'", (cid,))
        cur.execute("""INSERT INTO candidate_skill (candidate_id, skill_id, source)
                       SELECT %s, id, 'cv' FROM skill WHERE name = ANY(%s)
                       ON CONFLICT (candidate_id, skill_id) DO NOTHING""", (cid, parsed["skills"]))
        if parsed["experience_years"] > 0:
            cur.execute("UPDATE candidate SET exp_years=%s WHERE id=%s", (parsed["experience_years"], cid))
        if parsed["gpa"] is not None:
            cur.execute("UPDATE candidate SET gpa=%s WHERE id=%s", (parsed["gpa"], cid))
        conn.commit()
        n = refresh_matches(conn, cid)
        return {"cv_id": cv_id, "parsed": public, "health": health, "matches_updated": n}
    finally:
        conn.close()
        if os.path.exists(path):
            os.remove(path)


@router.post("/cv/demo-preset")
def load_demo_preset(preset: str = "realistic", user: dict = Depends(require_role("candidate"))):
    """Load a sample CV preset (realistic: ~78đ, perfect: 100đ, needs_work: 51đ) for testing/demo."""
    presets = {
        "realistic": ("cv_thuc_te.docx", "Nguyen_Minh_Anh_CV.docx"),
        "perfect": ("cv_tot.docx", "CV_Xuat_Sac_100.docx"),
        "needs_work": ("cv_trung_binh.docx", "CV_Can_Cai_Thien_51.docx"),
    }
    sample_file, display_name = presets.get(preset, presets["realistic"])
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_cvs"))
    path = os.path.join(base_dir, sample_file)
    if not os.path.exists(path):
        raise HTTPException(404, f"Sample CV file {sample_file} not found")

    conn = connect(retries=3)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM skill")
        vocab = [r[0] for r in cur.fetchall()]
        parsed = parse_cv(path, "docx", vocab=vocab)
        health = score_cv(parsed)
        cid = candidate_id(cur, user)
        public = {k: v for k, v in parsed.items() if k not in ("text", "text_nodiacritic")}

        cur.execute("""INSERT INTO cv_document (candidate_id, filename, raw_text, parsed_json, health_score,
                       health_issues_json) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (cid, display_name, parsed["text"], json.dumps(public),
                     health["score"], json.dumps(health)))
        cv_id = cur.fetchone()[0]

        cur.execute("DELETE FROM candidate_skill WHERE candidate_id=%s AND source='cv'", (cid,))
        cur.execute("""INSERT INTO candidate_skill (candidate_id, skill_id, source)
                       SELECT %s, id, 'cv' FROM skill WHERE name = ANY(%s)
                       ON CONFLICT (candidate_id, skill_id) DO NOTHING""", (cid, parsed["skills"]))
        if parsed["experience_years"] > 0:
            cur.execute("UPDATE candidate SET exp_years=%s WHERE id=%s", (parsed["experience_years"], cid))
        if parsed["gpa"] is not None:
            cur.execute("UPDATE candidate SET gpa=%s WHERE id=%s", (parsed["gpa"], cid))
        conn.commit()
        n = refresh_matches(conn, cid)
        return {"cv_id": cv_id, "filename": display_name, "parsed": public, "health": health, "matches_updated": n}
    finally:
        conn.close()

