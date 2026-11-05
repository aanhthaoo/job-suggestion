"""Shared helpers for ETL: skill normalisation, level/experience inference."""
import csv
import re
import unicodedata
from collections import Counter
from app.paths import DATA_DIR

MAIN_LOCATIONS = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Bắc Ninh", "Hưng Yên"]

CATEGORY_LABEL = {
    "kinh_doanh_bán_hàng_chăm_sóc_khách_hàng": "Kinh doanh - Bán hàng",
    "sản_xuất_lao_động_phổ_thông_cơ_khí": "Sản xuất - Cơ khí",
    "marketing_truyền_thông_quảng_cáo_nội_dung": "Marketing - Truyền thông",
    "tài_chính_kế_toán_ngân_hàng_bảo_hiểm": "Tài chính - Kế toán",
    "du_lịch_nhà_hàng_khách_sạn_dịch_vụ": "Du lịch - Dịch vụ",
    "thiết_kế_nghệ_thuật_giải_trí_truyền_hình_báo_chí": "Thiết kế - Nghệ thuật",
    "nhân_sự_hành_chính_pháp_chế_tư_vấn": "Nhân sự - Hành chính",
    "xây_dựng_kiến_trúc_bất_động_sản": "Xây dựng - Kiến trúc",
    "công_nghệ_thông_tin_kỹ_thuật_số": "Công nghệ thông tin",
    "logistics_vận_tải_chuỗi_cung_ứng": "Logistics - Vận tải",
    "kỹ_thuật_điện_điện_tử_viễn_thông": "Điện - Điện tử",
    "giáo_dục_đào_tạo_nghiên_cứu": "Giáo dục - Đào tạo",
    "y_tế_dược_chăm_sóc_sức_khỏe_công_nghệ_sinh_học": "Y tế - Dược",
    "ngôn_ngữ_dịch_thuật": "Ngôn ngữ - Dịch thuật",
    "nhóm_nghề_khác": "Khác",
    "nông_nghiệp_năng_lượng_môi_trường": "Nông nghiệp - Môi trường",
}

# manual merges of frequent spelling variants (lowercase key -> canonical)
MANUAL = {
    "autocad": "AutoCAD", "adobe photoshop": "Photoshop", "photoshop": "Photoshop",
    "capcut": "CapCut", "premiere": "Adobe Premiere", "adobe premiere": "Adobe Premiere",
    "adobe premiere pro": "Adobe Premiere", "after effect": "After Effects",
    "after effects": "After Effects", "adobe illustrator": "Illustrator", "illustrator": "Illustrator",
    "microsoft office": "Tin học văn phòng", "excel": "Excel", "microsoft excel": "Excel",
    "word": "Word", "powerpoint": "PowerPoint", "canva": "Canva", "seo": "SEO",
    "google ads": "Google Ads", "facebook ads": "Facebook Ads", "google analytics": "Google Analytics",
    "sketchup": "SketchUp", "revit": "Revit", "figma": "Figma", "indesign": "InDesign",
    "phần mềm kế toán": "Phần mềm kế toán", "ai": "AI", "sql": "SQL", "python": "Python",
    "phân tích dữ liệu": "Phân tích dữ liệu", "tiếng anh": "English", "english": "English",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def load_alias_map() -> dict:
    m = dict(MANUAL)
    p = DATA_DIR / "skill_alias.csv"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                can = row["canonical"].strip()
                m[can.lower()] = can
                for a in row["aliases"].split(","):
                    if a.strip():
                        m[a.strip().lower()] = can
    return m


def normalise_skill(raw: str, alias: dict):
    s = re.sub(r"\s+", " ", str(raw)).strip(" .;-•")
    if not s or len(s) > 40:
        return None
    low = s.lower()
    if "tin học văn phòng" in low or "office" in low and len(low) < 25:
        return "Tin học văn phòng"
    if low in alias:
        return alias[low]
    return s[0].upper() + s[1:]


def skill_type(name: str) -> str:
    low = name.lower()
    soft_kw = ("kỹ năng", "giao tiếp", "đàm phán", "thuyết phục", "làm việc nhóm", "teamwork",
               "communication", "problem solving", "sáng tạo", "chịu áp lực", "trách nhiệm")
    return "soft" if any(k in low for k in soft_kw) else "tech"


LEVEL_RULES = [
    ("Intern", r"thực tập|intern|tts\b"),
    ("Manager", r"trưởng phòng|giám đốc|manager|head of|director|trưởng bộ phận|quản lý"),
    ("Senior", r"senior|sr\.|chuyên viên cao cấp|lead\b|trưởng nhóm|chuyên gia"),
    ("Junior", r"junior|fresher|jr\.|mới ra trường|nhân viên|trợ lý|assistant|cộng tác viên"),
]
LEVELS = ["Intern", "Junior", "Mid", "Senior", "Manager"]


def infer_level(title: str, exp_years: float) -> str:
    t = (title or "").lower()
    for lvl, pat in LEVEL_RULES:
        if re.search(pat, t):
            # "nhân viên" with >=3y experience is really mid-level
            if lvl == "Junior" and exp_years >= 3:
                return "Mid"
            return lvl
    if exp_years >= 5:
        return "Senior"
    if exp_years >= 2:
        return "Mid"
    return "Junior"


def parse_exp_years(s) -> float:
    if not isinstance(s, str):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(năm|tháng)", s.lower())
    if not m:
        return 0.0
    v = float(m.group(1).replace(",", "."))
    return round(v / 12 if m.group(2) == "tháng" else v, 1)


def parse_education(s) -> str:
    t = str(s).lower()
    if "thạc" in t or "master" in t:
        return "Thạc sĩ"
    if "đại học" in t or "đh" in t:
        return "Đại học"
    if "cao đẳng" in t:
        return "Cao đẳng"
    if "trung cấp" in t:
        return "Trung cấp"
    if "thpt" in t or "trung học" in t or "cấp 3" in t:
        return "THPT"
    return "Không yêu cầu"


EDU_RANK = {"Không yêu cầu": 0, "THPT": 1, "Trung cấp": 2, "Cao đẳng": 3, "Đại học": 4, "Thạc sĩ": 5}

__all__ = ["Counter"]
