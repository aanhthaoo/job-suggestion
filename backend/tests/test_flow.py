"""End-to-end API flows: candidate journey, employer isolation, Gemini fallback, salary, BI endpoints, data quality."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.main import app
from ml import cv_suggest

client = TestClient(app)
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample_cvs" / "cv_tot.docx"


def _h(email, pw="demo123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def cand():
    return _h("candidate@demo.com")


@pytest.fixture(scope="module")
def uploaded(cand):
    if not SAMPLE.exists():
        import sys
        sys.path.insert(0, str(SAMPLE.parents[2] / "scripts"))
        import gen_sample_cvs
        gen_sample_cvs.main()
    with open(SAMPLE, "rb") as f:
        r = client.post("/api/v1/cv/upload", headers=cand, files={"file": ("cv_tot.docx", f)})
    assert r.status_code == 200, r.text
    return r.json()


def test_upload_cv_extracts_and_scores(uploaded):
    assert uploaded["health"]["score"] >= 80
    assert "Python" in uploaded["parsed"]["skills"] and uploaded["matches_updated"] > 0


def test_recommendations_sorted_with_reason(cand, uploaded):
    r = client.get("/api/v1/recommendations", params={"k": 10}, headers=cand).json()["recommendations"]
    assert len(r) == 10
    scores = [x["score"] for x in r]
    assert scores == sorted(scores, reverse=True)
    assert r[0]["reason"].startswith("Khớp") and r[0]["level"] in ("cao", "trung bình", "thấp")


def test_jobs_list_has_match_score_when_logged_in(cand, uploaded):
    items = client.get("/api/v1/jobs", params={"limit": 3}, headers=cand).json()["items"]
    assert all(0 <= j["match_score"] <= 1 for j in items)
    anon = client.get("/api/v1/jobs", params={"limit": 1}).json()["items"][0]
    assert "match_score" not in anon


def test_match_explanation(cand, uploaded):
    top = client.get("/api/v1/recommendations", params={"k": 1}, headers=cand).json()["recommendations"][0]
    ex = client.get(f"/api/v1/jobs/{top['job']['id']}/match", headers=cand).json()
    assert ex["score"] == pytest.approx(top["score"], abs=0.02) and "components" in ex


def test_candidate_endpoints_reject_other_roles():
    emp = _h("employer@demo.com")
    assert client.get("/api/v1/recommendations", headers=emp).status_code == 403
    assert client.get("/api/v1/recommendations").status_code == 401


def test_suggest_fallback_without_key(cand, uploaded, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    conn = connect(retries=2)
    cur = conn.cursor()
    cur.execute("DELETE FROM cv_suggestion")
    conn.commit()
    conn.close()
    top = client.get("/api/v1/recommendations", params={"k": 1}, headers=cand).json()["recommendations"][0]
    r = client.post("/api/v1/cv/suggest", params={"job_id": top["job"]["id"]}, headers=cand).json()
    assert r["source"] == "fallback"
    assert set(r["content"]) == {"summary", "add_keywords", "rewrite_bullets", "priority_fixes"}


def test_suggest_falls_back_when_gemini_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(cv_suggest, "_call_gemini", lambda p: (_ for _ in ()).throw(RuntimeError("quota")))
    res = cv_suggest.suggest({"title": "Dev"}, "cv", ["Docker"], ["Python"], ["x"])
    assert res["source"] == "fallback" and res["content"]["add_keywords"] == ["Docker"]


def test_salary_estimate_shape():
    j = client.get("/api/v1/jobs", params={"limit": 1}).json()["items"][0]
    r = client.get("/api/v1/salary/estimate", params={"job_id": j["id"]}).json()
    seg = r["segment"]
    assert seg["p25"] <= seg["p50"] <= seg["p75"] and r["estimate"] > 0
    assert client.get("/api/v1/salary/estimate").status_code == 400


def test_employer_isolation(cand, uploaded):
    a, b = _h("employer@demo.com"), _h("employer2@demo.com")
    body = {"title": "TEST Backend Dev", "category": "Công nghệ thông tin", "location": "Hà Nội",
            "description": "Python SQL backend", "skills": ["Python", "SQL"]}
    jid = client.post("/api/v1/employer/jobs", json=body, headers=a).json()["id"]
    try:
        ids_a = [j["id"] for j in client.get("/api/v1/employer/jobs", headers=a).json()]
        ids_b = [j["id"] for j in client.get("/api/v1/employer/jobs", headers=b).json()]
        assert jid in ids_a and jid not in ids_b
        ap = client.post("/api/v1/applications", json={"job_id": jid, "source": "search"}, headers=cand)
        assert ap.status_code == 200, ap.text
        assert client.post("/api/v1/applications", json={"job_id": jid}, headers=cand).status_code == 409
        ranked = client.get(f"/api/v1/employer/jobs/{jid}/candidates", headers=a).json()["candidates"]
        assert len(ranked) == 1 and ranked[0]["score"] > 0
        # employer B must not see or modify company A's data
        assert client.get(f"/api/v1/employer/jobs/{jid}/candidates", headers=b).status_code == 404
        app_id = ap.json()["id"]
        assert client.patch(f"/api/v1/applications/{app_id}", json={"status": "offer"}, headers=b).status_code == 404
        ok = client.patch(f"/api/v1/applications/{app_id}", json={"status": "interview"}, headers=a)
        assert ok.status_code == 200 and ok.json()["stage_reached"] == 2
        assert client.patch(f"/api/v1/applications/{app_id}", json={"status": "interview"}, headers=cand).status_code == 403
        mine = client.get("/api/v1/applications", headers=cand).json()
        assert any(x["id"] == app_id and x["status"] == "interview" for x in mine)
        # KPI is scoped by token company
        ka, kb = (client.get("/api/v1/employer/kpi", headers=h).json() for h in (a, b))
        assert ka["company_id"] != kb["company_id"] and ka["funnel"]["applied"] >= 1
    finally:
        conn = connect(retries=2)
        cur = conn.cursor()
        cur.execute("DELETE FROM job_posting WHERE id=%s", (jid,))
        conn.commit()
        conn.close()
        from ml.matching import invalidate
        invalidate()


def test_admin_and_market_endpoints():
    adm = _h("admin@demo.com")
    s = client.get("/api/v1/admin/stats", headers=adm).json()
    assert s["counts"]["job_posting"] >= 2000 and "vietjobs" in s["job_sources"]
    assert client.get("/api/v1/admin/stats", headers=_h("candidate@demo.com")).status_code == 403
    m = client.get("/api/v1/market/stats").json()
    assert len(m["skill_supply_demand"]) > 0 and len(m["salary_by_category"]) > 0


def test_data_quality():
    conn = connect(retries=2)
    cur = conn.cursor()
    checks = {
        "missing title/category/location": "SELECT COUNT(*) FROM job_posting WHERE title IS NULL OR category IS NULL OR location IS NULL",
        "duplicate job_key": "SELECT COUNT(*) FROM (SELECT job_key FROM job_posting GROUP BY 1 HAVING COUNT(*)>1) t",
        "negative or inverted salary": "SELECT COUNT(*) FROM job_posting WHERE salary_min < 0 OR salary_max < salary_min",
        "orphan skills (job_skill without job/skill)": "SELECT COUNT(*) FROM job_skill js LEFT JOIN job_posting j ON j.id=js.job_id LEFT JOIN skill s ON s.id=js.skill_id WHERE j.id IS NULL OR s.id IS NULL",
        "jobs without skills (vietjobs)": "SELECT COUNT(*) FROM job_posting j WHERE source='vietjobs' AND NOT EXISTS (SELECT 1 FROM job_skill WHERE job_id=j.id)",
        "unused skills": "SELECT COUNT(*) FROM skill s WHERE NOT EXISTS (SELECT 1 FROM job_skill WHERE skill_id=s.id)",
        "application stage/status mismatch": "SELECT COUNT(*) FROM application WHERE (status='offer' AND stage_reached<3) OR (status='interview' AND stage_reached<2)",
        "match_score out of [0,1]": "SELECT COUNT(*) FROM application WHERE match_score < 0 OR match_score > 1",
    }
    bad = {}
    for name, q in checks.items():
        cur.execute(q)
        n = cur.fetchone()[0]
        if n:
            bad[name] = n
    conn.close()
    assert not bad, bad


def test_profile_update_recomputes(cand):
    r = client.put("/api/v1/candidate/profile", headers=cand,
                   json={"expected_salary": 15, "location": "Hà Nội", "skills": ["Excel"]})
    assert r.status_code == 200
    assert "Excel" in [s["name"] for s in r.json()["skills"]]
    assert client.get("/api/v1/candidate/profile", headers=cand).json()["expected_salary"] == 15
    assert client.get("/api/v1/candidate/profile").status_code == 401
