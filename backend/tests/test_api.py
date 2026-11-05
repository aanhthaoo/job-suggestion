"""API smoke tests (need seeded Postgres: docker compose up -d postgres && python -m app.seed_db)."""
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email="candidate@demo.com", pw="demo123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return r.json()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_register_login():
    email = f"t_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "secret1", "full_name": "T U"})
    assert r.status_code == 200
    assert client.post("/api/v1/auth/register", json={"email": email, "password": "x12345", "full_name": "T"}).status_code == 400
    assert _login(email, "secret1")["user"]["role"] == "candidate"
    assert client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"}).status_code == 401


def test_me_requires_token():
    assert client.get("/api/v1/users/me").status_code == 401
    tok = _login()["access_token"]
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200 and r.json()["email"] == "candidate@demo.com"
    assert client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_jobs_search():
    r = client.get("/api/v1/jobs", params={"search": "Python", "limit": 5}).json()
    assert r["total"] > 0 and len(r["items"]) <= 5
    cat = r["items"][0]["category"]
    r2 = client.get("/api/v1/jobs", params={"category": cat, "limit": 3}).json()
    assert all(j["category"] == cat for j in r2["items"])


def test_job_detail():
    item = client.get("/api/v1/jobs", params={"limit": 1}).json()["items"][0]
    d = client.get(f"/api/v1/jobs/{item['id']}").json()
    assert d["title"] == item["title"] and isinstance(d["skills_required"], list)
    assert client.get("/api/v1/jobs/99999999").status_code == 404


def test_upload_rules():
    bad = client.post("/api/v1/cv/parse", files={"file": ("../../evil.exe", io.BytesIO(b"x"), "application/octet-stream")})
    assert bad.status_code == 400
    big = client.post("/api/v1/cv/parse", files={"file": ("a.pdf", io.BytesIO(b"0" * (5 * 1024 * 1024 + 1)), "application/pdf")})
    assert big.status_code == 413
