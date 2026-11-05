"""Golden-flow QA: drives the real UI (Edge via Playwright) and saves 8 screenshots to docs/qa/.

Needs: docker compose up (backend :8000, frontend :3000) + `pip install playwright`.
Flow: login -> upload CV -> recommendations -> job detail -> CV suggestion -> apply ->
      employer ranked candidates -> employer dashboard.
"""
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa"
CV = ROOT / "data" / "sample_cvs" / "cv_tot.docx"
WEB, API = "http://localhost:3000", "http://localhost:8000/api/v1"


def api_token(email):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": "demo123"}, timeout=30)
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


DEMO_TITLE = "Backend Developer (Python) - Demo"


def pick_job_for_demo():
    """The demo employer's showcase job (created once) so the golden flow has a high-fit posting."""
    h = api_token("employer@demo.com")
    mine = requests.get(f"{API}/employer/jobs", headers=h, timeout=30).json()
    for j in mine:
        if j["title"] == DEMO_TITLE:
            return j["id"]
    body = {"title": DEMO_TITLE, "category": "Công nghệ thông tin", "location": "Hà Nội", "level": "Junior",
            "exp_years_min": 1, "education": "Đại học", "salary_min": 15, "salary_max": 25,
            "description": "Xây dựng REST API bằng Python và FastAPI, làm việc với PostgreSQL, đóng gói bằng Docker.",
            "requirements": "Python, SQL, Docker, Git. Ưu tiên có dự án cá nhân.",
            "skills": ["Python", "SQL", "Docker", "Git", "FastAPI", "PostgreSQL", "Linux"]}
    r = requests.post(f"{API}/employer/jobs", json=body, headers=h, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def login(page, email):
    page.goto(f"{WEB}/auth/login")
    page.fill("input[type=email]", email)
    page.fill("input[type=password]", "demo123")
    page.click("button[type=submit]")
    page.wait_for_url(lambda u: "/auth/login" not in u, timeout=20000)


def shot(page, name):
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT / name), full_page=True)
    print("saved", name)


def main():
    job_id = pick_job_for_demo()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="vi-VN")
        page = ctx.new_page()

        login(page, "candidate@demo.com")
        page.wait_for_selector("text=Gợi ý việc làm cho bạn")
        shot(page, "01-dang-nhap-ung-vien.png")

        page.goto(f"{WEB}/profile")
        page.wait_for_selector("input[type=file]")
        page.set_input_files("input[type=file]", str(CV))
        page.wait_for_selector("text=Điểm sức khỏe CV", timeout=60000)
        page.wait_for_selector("text=Đã trích xuất")
        shot(page, "02-tai-cv-health.png")

        page.goto(f"{WEB}/recommendations")
        page.wait_for_selector("text=Khớp", timeout=60000)
        shot(page, "03-goi-y-viec-lam.png")

        page.goto(f"{WEB}/jobs/{job_id}?from=recommend")
        page.wait_for_selector("text=Vì sao khớp?", timeout=30000)
        shot(page, "04-chi-tiet-tin-diem-khop.png")

        page.click("text=Gợi ý sửa CV (AI)")
        page.wait_for_selector("text=Ưu tiên sửa", timeout=60000)
        shot(page, "05-goi-y-sua-cv.png")

        page.click("button:has-text('Ứng tuyển')")
        page.wait_for_selector("text=/Đã ứng tuyển|Đã ứng tuyển vị trí này/", timeout=30000)
        shot(page, "06-ung-tuyen.png")

        ctx.clear_cookies()
        page.evaluate("localStorage.clear()")
        login(page, "employer@demo.com")
        page.goto(f"{WEB}/employer/candidates?job={job_id}")
        try:
            page.get_by_text("Nguyễn Văn Demo").first.wait_for(timeout=30000)
        except Exception:
            print("DEBUG url:", page.url, " ", page.inner_text("body")[:600])
            raise
        shot(page, "07-nha-tuyen-dung-xep-hang.png")

        page.goto(f"{WEB}/employer/dashboard")
        page.wait_for_selector("text=Funnel tuyển dụng", timeout=30000)
        shot(page, "08-dashboard-nha-tuyen-dung.png")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
