"""CV parsing: text extraction (PDF/DOCX) + structured fields.

parse_cv() returns a fixed JSON-able dict:
{text, text_nodiacritic, skills, experience_years, education, gpa, contacts, sections, projects}
"""
import re
import unicodedata
from datetime import date
from typing import Dict, Iterable, List, Optional

# ----------------------------------------------------------------- aliases
_ALIAS_CACHE: Optional[Dict[str, str]] = None


def load_skill_aliases() -> Dict[str, str]:
    """alias(lowercase) -> canonical skill name (from data/skill_alias.csv, csv-module parsed)."""
    global _ALIAS_CACHE
    if _ALIAS_CACHE is None:
        from etl.common import load_alias_map  # shared with ETL so CV and JD skills agree
        _ALIAS_CACHE = load_alias_map()
    return _ALIAS_CACHE


# ----------------------------------------------------------------- text
def normalize_text(text: str) -> str:
    """NFC, drop control chars/HTML, collapse blanks. Keeps + # / @ . which skills/contacts need."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f​﻿]", "", text)
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def remove_diacritics(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")


def extract_text_from_pdf(file_path: str) -> str:
    import fitz  # PyMuPDF
    try:
        with fitz.open(file_path) as doc:
            return normalize_text("\n".join(page.get_text() for page in doc))
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Failed to extract PDF: {e}") from e


def extract_text_from_docx(file_path: str) -> str:
    from docx import Document
    try:
        doc = Document(file_path)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Failed to extract DOCX: {e}") from e
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:  # many CV templates are laid out in tables
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return normalize_text("\n".join(parts))


# ----------------------------------------------------------------- sections
SECTION_PATTERNS = {
    "summary": r"mục tiêu(?: nghề nghiệp)?|giới thiệu(?: bản thân)?|tóm tắt|career objective|objective|summary|profile|about me",
    "education": r"học vấn|trình độ học vấn|education|academic",
    "experience": r"kinh nghiệm(?: làm việc)?|quá trình làm việc|work experience|experience|employment",
    "skills": r"kỹ năng|skills?|technical skills|năng lực",
    "projects": r"dự án|đồ án|projects?|personal projects",
    "certifications": r"chứng chỉ|giải thưởng|certifications?|awards?|certificates",
}
_HEAD_RE = {k: re.compile(rf"^\W*(?:{p})\W*$", re.IGNORECASE) for k, p in SECTION_PATTERNS.items()}


def split_sections(text: str) -> Dict[str, str]:
    """Split by heading lines (short line that is exactly a known heading). Preamble -> 'header'."""
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"
    for line in text.split("\n"):
        stripped = line.strip()
        hit = None
        if 0 < len(stripped) <= 40:
            for name, rx in _HEAD_RE.items():
                if rx.match(stripped):
                    hit = name
                    break
        if hit:
            current = hit
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


# ----------------------------------------------------------------- fields
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}(?!\d)")


def extract_contacts(text: str) -> Dict[str, Optional[str]]:
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    linkedin = re.search(r"linkedin\.com/in/[\w-]+", text, re.IGNORECASE)
    github = re.search(r"github\.com/[\w-]+", text, re.IGNORECASE)
    return {"email": email.group(0) if email else None,
            "phone": re.sub(r"[\s.-]", "", phone.group(0)) if phone else None,
            "linkedin": linkedin.group(0) if linkedin else None,
            "github": github.group(0) if github else None}


def extract_gpa(text: str) -> Optional[float]:
    """GPA normalised to a 4.0 scale. Accepts 'GPA: 3.4/4', 'GPA 8.2/10', 'Điểm trung bình: 3.2'."""
    m = re.search(r"(?:gpa|điểm trung bình|điểm tb|cgpa)\s*[:\-]?\s*(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:/\s*(\d{1,2}))?",
                  text, re.IGNORECASE)
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    scale = float(m.group(2)) if m.group(2) else (10.0 if v > 4.0 else 4.0)
    if scale <= 0 or v > scale:
        return None
    return round(v / scale * 4.0, 2)


_DEGREE_RE = re.compile(r"(?:tiến sĩ|thạc sĩ|cử nhân|kỹ sư|đại học|cao đẳng|trung cấp|bachelor|master|phd|"
                        r"university|college|học viện)", re.IGNORECASE)


def extract_education(text: str, sections: Optional[Dict[str, str]] = None) -> List[str]:
    sections = sections if sections is not None else split_sections(text)
    source = sections.get("education") or text
    lines = [ln.strip(" -•*\t") for ln in source.split("\n") if _DEGREE_RE.search(ln)]
    seen, out = set(), []
    for ln in lines:
        if ln.lower() not in seen:
            seen.add(ln.lower())
            out.append(ln[:160])
    return out[:3]


_MONTHS = r"(?:0?[1-9]|1[0-2])"
_RANGE_RE = re.compile(rf"(?:({_MONTHS})\s*[/.-]\s*)?((?:19|20)\d{{2}})\s*(?:-|–|—|đến|to)\s*"
                       rf"(?:(?:({_MONTHS})\s*[/.-]\s*)?((?:19|20)\d{{2}})|(nay|hiện tại|present|now))", re.IGNORECASE)


def extract_experience_years(text: str, sections: Optional[Dict[str, str]] = None) -> float:
    """Explicit 'N năm kinh nghiệm' wins; otherwise sum date ranges in the experience section."""
    m = re.search(r"(\d+(?:[.,]\d)?)\+?\s*(?:năm|years?|yrs?)\s*(?:kinh nghiệm|of experience|experience|exp)", text,
                  re.IGNORECASE) or re.search(r"(?:kinh nghiệm|experience)\s*[:\-]?\s*(\d+(?:[.,]\d)?)\s*(?:năm|years?)",
                                              text, re.IGNORECASE)
    if m:
        return min(float(m.group(1).replace(",", ".")), 40.0)
    sections = sections if sections is not None else split_sections(text)
    source = sections.get("experience", "")
    today = date.today()
    months = 0
    for mm in _RANGE_RE.finditer(source):
        m1, y1, m2, y2, now = mm.groups()
        start = int(y1) * 12 + (int(m1) if m1 else 1)
        end = today.year * 12 + today.month if now else int(y2) * 12 + (int(m2) if m2 else 12)
        if end >= start:
            months += end - start + (1 if m1 or m2 else 0)
    return round(min(months / 12.0, 40.0), 1)


def extract_projects(text: str, sections: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """A project = a non-bullet line (title) followed by its bullet lines (description)."""
    sections = sections if sections is not None else split_sections(text)
    src = sections.get("projects", "")
    projects: List[Dict[str, str]] = []
    for line in src.split("\n"):
        s = line.strip()
        if not s:
            continue
        is_bullet = s[0] in "-•*–"
        if is_bullet and projects:
            projects[-1]["description"] += (" " if projects[-1]["description"] else "") + s.lstrip("-•*– ")
        elif not is_bullet:
            projects.append({"name": s[:120], "description": ""})
    return projects[:8]


def extract_skills(text: str, skill_aliases: Optional[Dict[str, str]] = None,
                   vocab: Optional[Iterable[str]] = None) -> List[str]:
    """Match aliases with token boundaries (so 'C++', 'Node.js' work). `vocab` restricts/extends canonicals."""
    aliases = dict(skill_aliases if skill_aliases is not None else load_skill_aliases())
    if vocab:
        for v in vocab:
            aliases.setdefault(v.lower(), v)
    low = text.lower()
    found = set()
    for alias, canonical in aliases.items():
        if len(alias) <= 2:
            continue  # 'py', 'ts', 'ml' collide with ordinary words
        if re.search(r"(?<![\w+#])" + re.escape(alias) + r"(?![\w+#])", low):
            found.add(canonical)
    return sorted(found)


# ----------------------------------------------------------------- main
def parse_text(text: str, vocab: Optional[Iterable[str]] = None) -> Dict:
    """Parse already-extracted text (used by tests and by parse_cv)."""
    sections = split_sections(text)
    return {
        "text": text,
        "text_nodiacritic": remove_diacritics(text),
        "skills": extract_skills(text, vocab=vocab),
        "experience_years": extract_experience_years(text, sections),
        "education": extract_education(text, sections),
        "gpa": extract_gpa(text),
        "contacts": extract_contacts(text),
        "sections": sections,
        "projects": extract_projects(text, sections),
    }


def parse_cv(file_path: str, file_type: str = "pdf", vocab: Optional[Iterable[str]] = None) -> Dict:
    ft = file_type.lower()
    if ft == "pdf":
        text = extract_text_from_pdf(file_path)
    elif ft == "docx":
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parse_text(text, vocab=vocab)


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1:
        r = parse_cv(sys.argv[1], sys.argv[1].rsplit(".", 1)[-1])
        r.pop("text"), r.pop("text_nodiacritic")
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print("Usage: python -m app.cv_parser <cv.pdf|cv.docx>")
