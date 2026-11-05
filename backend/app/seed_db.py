"""Apply schema and seed data. Idempotent; run on backend start: python -m app.seed_db

SEED_MODE=schema -> only apply schema + demo users (used by tests).
"""
import os
from pathlib import Path

from .db import connect
from .security import hash_password

SCHEMA = Path(__file__).resolve().parents[1] / "db" / "schema.sql"

DEMO = [  # email, password, role, full_name
    ("candidate@demo.com", "demo123", "candidate", "Nguyễn Minh Anh"),
    ("employer@demo.com", "demo123", "employer", None),
    ("employer2@demo.com", "demo123", "employer", None),
    ("admin@demo.com", "demo123", "admin", None),
]


def _seed_candidate_cv(cur, cid: int):
    import json
    cur.execute("SELECT 1 FROM cv_document WHERE candidate_id=%s", (cid,))
    if cur.fetchone():
        return

    parsed_json = {
        "full_name": "Nguyễn Minh Anh",
        "title": "Fullstack Web & Backend Developer",
        "contacts": {
            "email": "minhanh.dev@gmail.com",
            "phone": "0912 345 678",
            "github": "github.com/minhanh-dev",
            "linkedin": "linkedin.com/in/minhanh-dev",
            "address": "Quận Cầu Giấy, Hà Nội"
        },
        "summary": "Kỹ sư phần mềm với hơn 2 năm kinh nghiệm thực chiến phát triển ứng dụng web và hệ thống API backend hiệu năng cao. Có kinh nghiệm tối ưu hóa cơ sở dữ liệu PostgreSQL và triển khai container hóa với Docker. Mong muốn cống hiến năng lực chuyên môn, tinh thần nhiệt tình và ham học hỏi để xây dựng các sản phẩm công nghệ có giá trị cao cho doanh nghiệp.",
        "education": [
            {
                "degree": "Cử nhân Công nghệ thông tin",
                "school": "Đại học Bách Khoa Hà Nội (HUST)",
                "period": "2019 - 2023",
                "gpa": "3.40 / 4.0 (Xếp loại: Giỏi)",
                "honors": "Học bổng Khuyến khích học tập kỳ 2021-2022"
            }
        ],
        "experience": [
            {
                "position": "Fullstack Developer",
                "company": "Công ty Cổ phần Giải pháp Công nghệ TechCorp",
                "period": "07/2023 - Hiện tại",
                "location": "Hà Nội",
                "responsibilities": [
                    "Tham gia phát triển hệ sinh thái quản lý bán hàng đa kênh sử dụng React, TypeScript và Node.js.",
                    "Thiết kế và triển khai 12 REST API phục vụ phân hệ thanh toán, xử lý hơn 1.000 đơn hàng mỗi ngày.",
                    "Tối ưu hóa câu truy vấn cơ sở dữ liệu PostgreSQL, giúp giảm 35% độ trễ phản hồi của hệ thống.",
                    "Phối hợp với đội ngũ QA và DevOps đóng gói dịch vụ bằng Docker, cấu hình CI/CD trên GitHub Actions."
                ]
            },
            {
                "position": "Thực tập sinh Lập trình Web",
                "company": "Công ty TNHH Phần mềm VNext Global",
                "period": "06/2022 - 05/2023",
                "location": "Hà Nội",
                "responsibilities": [
                    "Phát triển giao diện người dùng Responsive cho hệ thống CRM nội bộ bằng React và Tailwind CSS.",
                    "Xây dựng các API backend tích hợp cơ sở dữ liệu MySQL và cache Redis.",
                    "Tham gia viết tài liệu kỹ thuật API Swagger và quy trình kiểm thử đơn vị (Unit Test)."
                ]
            }
        ],
        "projects": [
            {
                "name": "Hệ thống Tuyển dụng & Gợi ý Việc làm Thông minh",
                "role": "Core Developer (Đồ án Tốt nghiệp)",
                "tech_stack": "Next.js, FastAPI, PostgreSQL, scikit-learn, Docker",
                "description": "Xây dựng nền tảng kết nối ứng viên và nhà tuyển dụng, tích hợp thuật toán AI Matching 5 thành phần để xếp hạng độ phù hợp của ứng viên theo kỹ năng và kinh nghiệm."
            },
            {
                "name": "Sàn Thương mại Điện tử Mini (E-Commerce Platform)",
                "role": "Fullstack Developer (Dự án Cá nhân)",
                "tech_stack": "React, Node.js, Express, MongoDB, Redis, Stripe",
                "description": "Phát triển ứng dụng mua sắm trực tuyến với giỏ hàng thời gian thực, tích hợp cổng thanh toán trực tuyến, quản lý kho hàng và phân quyền người dùng."
            }
        ],
        "skills": [
            "Python", "FastAPI", "React", "TypeScript", "Next.js", "Node.js", "PostgreSQL",
            "Docker", "Git", "Redis", "MySQL", "Linux", "REST API", "Tailwind CSS", "SQL"
        ],
        "soft_skills": [
            "Làm việc nhóm (Agile/Scrum)", "Tư duy giải quyết vấn đề", "Giao tiếp & Thuyết trình kỹ thuật", "Quản lý thời gian"
        ],
        "languages": [
            "Tiếng Anh (IELTS 7.0 - Giao tiếp và đọc hiểu tài liệu kỹ thuật thành thạo)",
            "Tiếng Việt (Bản ngữ)"
        ],
        "certifications": [
            "AWS Certified Cloud Practitioner (2024)",
            "IELTS Academic 7.0 Overall (2023)"
        ],
        "experience_years": 2.0,
        "gpa": 3.4
    }

    health_issues = {
        "score": 78.0,
        "breakdown": {
            "sections": 20.0,
            "contact": 15.0,
            "skills": 15.0,
            "quantified": 10.0,
            "length": 15.0,
            "cliche": 3.0
        },
        "issues": [
            "Mới có 2 số liệu định lượng (cần ≥4) — ví dụ 'tăng 30% doanh thu', 'phục vụ 500 khách/tháng', 'giảm 25% thời gian phản hồi'",
            "Cụm từ sáo rỗng: 'nhiệt tình', 'ham học hỏi' — nên thay thế bằng dự án cụ thể hoặc dẫn chứng thành tích thực tế"
        ]
    }

    raw_cv_text = """Nguyễn Minh Anh
Email: minhanh.dev@gmail.com | Điện thoại: 0912 345 678 | github.com/minhanh-dev | linkedin.com/in/minhanh-dev
Địa chỉ: Quận Cầu Giấy, Hà Nội | Vị trí: Fullstack Web & Backend Developer

Mục tiêu nghề nghiệp
Kỹ sư phần mềm với hơn 2 năm kinh nghiệm thực chiến phát triển ứng dụng web và hệ thống API backend hiệu năng cao. Có kinh nghiệm tối ưu hóa cơ sở dữ liệu PostgreSQL và triển khai container hóa với Docker. Mong muốn cống hiến năng lực chuyên môn, tinh thần nhiệt tình và ham học hỏi để xây dựng các sản phẩm công nghệ có giá trị cao cho doanh nghiệp.

Học vấn
Cử nhân Công nghệ thông tin - Đại học Bách Khoa Hà Nội (HUST) (2019 - 2023)
GPA: 3.40 / 4.0 (Xếp loại: Giỏi)
Học bổng Khuyến khích học tập kỳ 2021-2022

Kinh nghiệm làm việc
Fullstack Developer - Công ty Cổ phần Giải pháp Công nghệ TechCorp (07/2023 - Hiện tại)
- Tham gia phát triển hệ sinh thái quản lý bán hàng đa kênh sử dụng React, TypeScript và Node.js.
- Thiết kế và triển khai 12 REST API phục vụ phân hệ thanh toán, xử lý hơn 1.000 đơn hàng mỗi ngày.
- Tối ưu hóa câu truy vấn cơ sở dữ liệu PostgreSQL, giúp giảm 35% độ trễ phản hồi của hệ thống.
- Phối hợp với đội ngũ QA và DevOps đóng gói dịch vụ bằng Docker, cấu hình CI/CD trên GitHub Actions.

Thực tập sinh Lập trình Web - Công ty TNHH Phần mềm VNext Global (06/2022 - 05/2023)
- Phát triển giao diện người dùng Responsive cho hệ thống CRM nội bộ bằng React và Tailwind CSS.
- Xây dựng các API backend tích hợp cơ sở dữ liệu MySQL và cache Redis.
- Tham gia viết tài liệu kỹ thuật API Swagger và quy trình kiểm thử đơn vị (Unit Test).

Dự án
Hệ thống Tuyển dụng & Gợi ý Việc làm Thông minh
- Xây dựng nền tảng kết nối ứng viên và nhà tuyển dụng, tích hợp thuật toán AI Matching 5 thành phần để xếp hạng độ phù hợp của ứng viên theo kỹ năng và kinh nghiệm.

Sàn Thương mại Điện tử Mini (E-Commerce Platform)
- Phát triển ứng dụng mua sắm trực tuyến với giỏ hàng thời gian thực, tích hợp cổng thanh toán trực tuyến, quản lý kho hàng và phân quyền người dùng.

Kỹ năng
Python, FastAPI, React, TypeScript, Next.js, Node.js, PostgreSQL, Docker, Git, Redis, MySQL, Linux, REST API, Tailwind CSS, SQL

Chứng chỉ
AWS Certified Cloud Practitioner (2024)
IELTS Academic 7.0 Overall (2023)
"""

    cur.execute("""INSERT INTO cv_document (candidate_id, filename, raw_text, parsed_json, health_score, health_issues_json)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (cid, "Nguyen_Minh_Anh_CV.pdf", raw_cv_text, json.dumps(parsed_json), 78.0, json.dumps(health_issues)))

    for s in parsed_json["skills"]:
        cur.execute("""INSERT INTO candidate_skill (candidate_id, skill_id, source)
                       SELECT %s, id, 'cv' FROM skill WHERE lower(name) = lower(%s)
                       ON CONFLICT DO NOTHING""", (cid, s))


def apply_schema(cur):
    # drop the legacy (pre-v2) text-keyed tables if present
    cur.execute("""SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='full_name'""")
    if cur.fetchone():
        cur.execute("DROP TABLE IF EXISTS applications, job_skills, jobs, companies, users CASCADE")
    cur.execute(SCHEMA.read_text(encoding="utf-8"))


def seed_demo_users(cur):
    # demo employers get the companies with the most applications, so dashboards are not empty
    cur.execute("""SELECT j.company_id FROM job_posting j JOIN application a ON a.job_id=j.id
                   WHERE j.source <> 'employer' GROUP BY j.company_id ORDER BY COUNT(*) DESC, j.company_id LIMIT 2""")
    comps = [r[0] for r in cur.fetchall()]
    emp_i = 0
    for email, pw, role, name in DEMO:
        company_id = None
        if role == "employer" and emp_i < len(comps):
            company_id = comps[emp_i]
            emp_i += 1
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            if role == "employer" and company_id:
                cur.execute("UPDATE users SET company_id=%s WHERE id=%s", (company_id, uid))
            elif role == "candidate":
                cur.execute("SELECT id FROM candidate WHERE user_id=%s", (uid,))
                crow = cur.fetchone()
                if crow:
                    _seed_candidate_cv(cur, crow[0])
            continue
        cur.execute("INSERT INTO users (email, password_hash, role, company_id) VALUES (%s,%s,%s,%s) RETURNING id",
                    (email, hash_password(pw), role, company_id))
        uid = cur.fetchone()[0]
        if role == "candidate":
            cur.execute("""INSERT INTO candidate (user_id, full_name, location, exp_years, education, major, gpa, expected_salary)
                        VALUES (%s,%s,'Hà Nội',2.0,'Đại học Bách Khoa Hà Nội','Công nghệ thông tin',3.40,18.0) RETURNING id""", (uid, name))
            cid = cur.fetchone()[0]
            _seed_candidate_cv(cur, cid)


def counts(cur):
    out = {}
    for t in ("company", "job_posting", "skill", "job_skill", "candidate", "candidate_skill", "application", "users"):
        cur.execute(f"SELECT COUNT(*) FROM {t}")  # noqa: S608 fixed names
        out[t] = cur.fetchone()[0]
    return out


def seed():
    mode = os.getenv("SEED_MODE", "full")
    conn = connect()
    cur = conn.cursor()
    apply_schema(cur)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM job_posting")
    has_jobs = cur.fetchone()[0] > 0
    conn.close()
    if mode != "schema":
        if not has_jobs:
            from etl import load_jobs
            load_jobs.main()
        from etl import synth_candidates, synth_applications
        synth_candidates.main()
        synth_applications.main()
    conn = connect()
    cur = conn.cursor()
    seed_demo_users(cur)
    conn.commit()
    result = counts(cur)
    conn.close()
    return result


if __name__ == "__main__":
    print("Seeded PostgreSQL:", seed())
