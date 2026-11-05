"""CV health score (0-100) from 6 transparent rules; every lost point comes with a concrete message."""
import re
from typing import Dict, List

REQUIRED_SECTIONS = {"education": "Học vấn", "experience": "Kinh nghiệm", "skills": "Kỹ năng"}
CLICHES = ["chăm chỉ", "nhiệt tình", "ham học hỏi", "cầu tiến", "năng động", "chịu khó", "có trách nhiệm",
           "team player", "hard-working", "hard working", "fast learner", "passionate", "detail-oriented",
           "giao tiếp tốt", "làm việc nhóm tốt"]
_QUANT_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|\+|triệu|tỷ|tr\b|k\b|users?|người|khách|dự án|projects?|"
                       r"đơn|lần|tháng|năm|giờ|x\b)", re.IGNORECASE)

MAX_POINTS = {"sections": 20, "contact": 15, "skills": 15, "quantified": 20, "length": 15, "cliche": 15}


def _rule_sections(parsed: Dict):
    secs = parsed.get("sections", {})
    missing = [label for key, label in REQUIRED_SECTIONS.items() if key not in secs]
    pts = MAX_POINTS["sections"] * (len(REQUIRED_SECTIONS) - len(missing)) / len(REQUIRED_SECTIONS)
    if "projects" not in secs and "experience" not in secs:
        pts = max(0, pts - 4)
    msgs = [f"Thiếu mục '{m}' — thêm tiêu đề riêng cho mục này" for m in missing]
    if "projects" not in secs:
        msgs.append("Chưa có mục 'Dự án' — thêm 1-3 dự án tiêu biểu kèm công nghệ và kết quả")
    return pts, msgs


def _rule_contact(parsed: Dict):
    c = parsed.get("contacts", {})
    pts, msgs = MAX_POINTS["contact"], []
    if not c.get("email"):
        pts -= 8
        msgs.append("Không tìm thấy email liên hệ")
    if not c.get("phone"):
        pts -= 7
        msgs.append("Không tìm thấy số điện thoại")
    return max(pts, 0), msgs


def _rule_skills(parsed: Dict):
    n = len(parsed.get("skills", []))
    pts = MAX_POINTS["skills"] * min(n, 5) / 5
    return pts, ([f"Chỉ nhận diện được {n}/5 kỹ năng tối thiểu — liệt kê rõ công cụ/công nghệ đã dùng"] if n < 5 else [])


def _rule_quantified(parsed: Dict):
    n = len(_QUANT_RE.findall(parsed.get("text", "")))
    pts = MAX_POINTS["quantified"] * min(n, 4) / 4
    return pts, ([f"Mới có {n} số liệu định lượng (cần ≥4) — ví dụ 'tăng 30% doanh thu', 'phục vụ 500 khách/tháng'"]
                 if n < 4 else [])


def _rule_length(parsed: Dict):
    words = len(parsed.get("text", "").split())
    if 150 <= words <= 700:
        return MAX_POINTS["length"], []
    if words < 150:
        return MAX_POINTS["length"] * words / 150, [f"CV quá ngắn ({words} từ) — nên từ 150 đến 700 từ"]
    return max(0, MAX_POINTS["length"] * (1 - (words - 700) / 700)), [f"CV quá dài ({words} từ) — rút gọn xuống dưới 700 từ"]


def _rule_cliche(parsed: Dict):
    low = parsed.get("text", "").lower()
    hits = [c for c in CLICHES if c in low]
    pts = max(0, MAX_POINTS["cliche"] - 5 * len(hits))
    return pts, ([f"Cụm sáo rỗng: {', '.join(hits)} — thay bằng bằng chứng cụ thể" ] if hits else [])


RULES = [("sections", _rule_sections), ("contact", _rule_contact), ("skills", _rule_skills),
         ("quantified", _rule_quantified), ("length", _rule_length), ("cliche", _rule_cliche)]


def score_cv(parsed: Dict) -> Dict:
    """-> {score: float 0-100, breakdown: {rule: points}, issues: [str]}"""
    breakdown, issues = {}, []  # type: Dict[str, float], List[str]
    for name, fn in RULES:
        pts, msgs = fn(parsed)
        breakdown[name] = round(pts, 1)
        issues.extend(msgs)
    return {"score": round(sum(breakdown.values()), 1), "breakdown": breakdown, "issues": issues}
