"""CV parser + CV health tests on the 3 sample CVs (good / average / poor)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.cv_parser import (extract_contacts, extract_experience_years, extract_gpa,  # noqa: E402
                           extract_skills, parse_cv, parse_text, split_sections)
from ml.cv_health import score_cv  # noqa: E402

SAMPLES = ROOT / "data" / "sample_cvs"


@pytest.fixture(scope="session", autouse=True)
def _samples():
    if not (SAMPLES / "cv_tot.docx").exists():
        import gen_sample_cvs
        gen_sample_cvs.main()


def _parse(name):
    return parse_cv(str(SAMPLES / name), "docx")


def test_sections_split():
    secs = split_sections(_parse("cv_tot.docx")["text"])
    for k in ("education", "experience", "skills", "projects", "certifications"):
        assert k in secs


def test_contacts_and_gpa():
    p = _parse("cv_tot.docx")
    assert p["contacts"]["email"] == "minhanh.dev@gmail.com"
    assert p["contacts"]["phone"] == "0912345678"
    assert p["contacts"]["github"] == "github.com/minhanh-dev"
    assert p["gpa"] == 3.4
    assert extract_gpa("GPA: 8.0/10") == 3.2
    assert extract_gpa("no gpa here") is None


def test_skills_extraction_with_symbols():
    sk = extract_skills("Dùng C++, Node.js và CI/CD, javascript, reactjs; không biết Rust")
    assert {"Node.js", "CI/CD", "React", "JavaScript"} <= set(sk)
    assert "Python" not in sk


def test_experience_years_from_date_ranges():
    p = _parse("cv_tot.docx")
    assert p["experience_years"] >= 3  # "3 năm kinh nghiệm" in summary
    txt = "Kinh nghiệm\nDev - A (01/2020 - 01/2022)\nDev - B (2022 - 2023)\n"
    assert 2.5 <= extract_experience_years(txt) <= 4.5


def test_projects_and_education():
    p = _parse("cv_tot.docx")
    assert len(p["projects"]) == 2
    assert p["projects"][0]["name"].startswith("Hệ thống gợi ý")
    assert any("Bách Khoa" in e for e in p["education"])


def test_parse_result_schema():
    keys = {"text", "text_nodiacritic", "skills", "experience_years", "education", "gpa",
            "contacts", "sections", "projects"}
    assert keys <= set(_parse("cv_trung_binh.docx"))


def test_health_ordering_good_average_poor():
    good = score_cv(_parse("cv_tot.docx"))["score"]
    avg = score_cv(_parse("cv_trung_binh.docx"))["score"]
    poor = score_cv(_parse("cv_kem.docx"))["score"]
    assert good > avg > poor, (good, avg, poor)
    assert good >= 80 and poor <= 30


def test_health_issues_are_specific():
    r = score_cv(_parse("cv_kem.docx"))
    joined = " | ".join(r["issues"])
    assert "email" in joined and "điện thoại" in joined and "sáo rỗng" in joined
    assert score_cv(parse_text(""))["score"] < 20
