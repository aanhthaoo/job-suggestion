"""Load real job postings (VietJobs, HuggingFace) into Postgres.

Sampled (<=5000 rows, capped per category). VietJobs has no posting date nor company,
so `posted_at` (spread over 12 months, seed 42) and company are SIMULATED and
documented as such in the report. Everything else (title, JD, skills, salary, benefits, etc.) is real.
Run: python -m etl.load_jobs
"""
import ast
import random
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
from psycopg2.extras import execute_values

from app.db import connect
from app.paths import DATA_DIR
from .common import (CATEGORY_LABEL, MAIN_LOCATIONS, infer_level, load_alias_map, normalise_skill,
                     parse_education, parse_exp_years, skill_type)

CAP_PER_CATEGORY = 330  # 16 categories -> ~4000+ rows
MIN_SKILL_FREQ = 60
SEED = 42
COMPANY_PREFIX = ["Công ty TNHH", "Công ty CP", "Tập đoàn", "Công ty"]
COMPANY_CORE = ["An Phát", "Việt Tiến", "Hoàng Gia", "Minh Long", "Đại Dương", "Thành Công", "Tân Á",
                "Bảo Minh", "Phương Nam", "Hải Đăng", "Kim Cương", "Sao Mai", "Đông Dương", "Thiên Long",
                "Á Châu", "Trường Sinh", "Hưng Thịnh", "Gia Bảo", "Nam Việt", "Quang Minh"]
SIZES = ["1-50", "50-200", "200-1000", "1000+"]


def get_csv() -> str:
    p = DATA_DIR / "raw" / "VietJobs.csv"
    if not p.exists():
        from huggingface_hub import hf_hub_download
        hf_hub_download("dinhieufam/VietJobs", "VietJobs.csv", repo_type="dataset", local_dir=str(DATA_DIR / "raw"))
    return str(p)


def norm_location(s) -> str:
    t = str(s).lower().split(",")[0].strip()
    t = {"hà đông": "hà nội", "cầu giấy": "hà nội"}.get(t, t)
    for loc in MAIN_LOCATIONS:
        if loc.lower() == t:
            return loc
    return "Khác"


def parse_skills(v, alias):
    if not isinstance(v, str):
        return []
    try:
        items = ast.literal_eval(v)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for it in items:
        n = normalise_skill(it, alias)
        if n and n not in out:
            out.append(n)
    return out


def parse_benefits(v) -> Optional[str]:
    if not isinstance(v, str) or not v.strip():
        return None
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        try:
            items = ast.literal_eval(v)
            if isinstance(items, list) and items:
                cleaned = [str(x).strip() for x in items if str(x).strip()]
                if cleaned:
                    return "\n".join(f"• {x}" for x in cleaned)
        except Exception:  # noqa: BLE001
            pass
    return v if v.lower() != "nan" else None


def parse_soft_skills(v) -> List[str]:
    if not isinstance(v, str) or not v.strip():
        return []
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        try:
            items = ast.literal_eval(v)
            if isinstance(items, list):
                return [str(x).strip() for x in items if str(x).strip()]
        except Exception:  # noqa: BLE001
            pass
    if v.lower() == "nan":
        return []
    return [x.strip() for x in v.split(",") if x.strip()]


def parse_languages(v) -> Optional[str]:
    if not isinstance(v, str) or not v.strip():
        return None
    v = v.strip()
    if v.lower() in ("nan", "unk", "none"):
        return None
    langs = [x.strip().title() for x in v.split(",") if x.strip() and x.strip().lower() != "unk"]
    return ", ".join(langs) if langs else None


def parse_contract(v) -> Optional[str]:
    if not isinstance(v, str) or not v.strip() or v.lower() == "nan":
        return "Toàn thời gian"
    return v.strip()


def parse_working_hours(v) -> Optional[str]:
    if not isinstance(v, str) or not v.strip() or v.lower() == "nan":
        return None
    return v.strip()


def main():
    rng = random.Random(SEED)
    alias = load_alias_map()
    df = pd.read_csv(get_csv())
    df = df[(df.country == "Việt Nam") & df.description.notna() & df.job_title.notna()]
    df = df.drop_duplicates(subset=["job_title", "description"])
    df["skills"] = df.technical_skills.map(lambda v: parse_skills(v, alias))
    freq = Counter(s for sk in df.skills for s in sk)  # vocabulary from the full dataset
    vocab = {s for s, c in freq.items() if c >= MIN_SKILL_FREQ}
    df["skills"] = df.skills.map(lambda sk: [s for s in sk if s in vocab][:12])
    df = df[df.skills.map(len) >= 2]
    df = pd.concat([g.sample(min(len(g), CAP_PER_CATEGORY), random_state=SEED)
                    for _, g in df.groupby("category")]).reset_index(drop=True)
    vocab = {s for sk in df.skills for s in sk}
    print(f"jobs kept: {len(df)}, skill vocab: {len(vocab)}")

    conn = connect()
    cur = conn.cursor()
    # skills
    execute_values(cur, "INSERT INTO skill (name, type) VALUES %s ON CONFLICT (name) DO NOTHING",
                   [(s, skill_type(s)) for s in sorted(vocab)])
    cur.execute("SELECT name, id FROM skill")
    skill_id = dict(cur.fetchall())

    # companies (simulated: VietJobs has no company column)
    companies = {}
    for cat in df.category.unique():
        for i in range(12):
            name = f"{rng.choice(COMPANY_PREFIX)} {rng.choice(COMPANY_CORE)} {CATEGORY_LABEL.get(cat, 'Khác').split(' - ')[0]} {i+1}"
            companies.setdefault(name, (name, rng.choice(MAIN_LOCATIONS), CATEGORY_LABEL.get(cat, "Khác"), rng.choice(SIZES)))
    execute_values(cur, "INSERT INTO company (name, location, industry, size) VALUES %s ON CONFLICT (name) DO NOTHING",
                   list(companies.values()))
    cur.execute("SELECT name, id, industry FROM company")
    comp_by_ind = {}
    for n, i, ind in cur.fetchall():
        comp_by_ind.setdefault(ind, []).append(i)

    now = datetime.now(timezone.utc)
    rows, job_skills_rows = [], []
    for idx, r in df.iterrows():
        label = CATEGORY_LABEL.get(r.category, "Khác")
        exp = parse_exp_years(r.experience_required)
        smin = r.salary_min if 0 < r.salary_min <= 300 else None
        smax = r.salary_max if 0 < r.salary_max <= 300 else None
        if smin and smax and smin > smax:
            smin, smax = smax, smin
        if (smin is None) != (smax is None):
            smin = smax = smin or smax
        key = f"vj-{idx:05d}"
        posted = now - timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
        benefits = parse_benefits(r.benefits)
        contract = parse_contract(r.contract_type)
        hours = parse_working_hours(r.working_hours)
        soft = parse_soft_skills(r.soft_skills)
        langs = parse_languages(r.languages_required)

        rows.append((key, rng.choice(comp_by_ind[label]), str(r.job_title)[:200], label, norm_location(r.location),
                     infer_level(r.job_title, exp), exp, parse_education(r.qualifications), smin, smax,
                     str(r.description), str(r.requirements_text) if isinstance(r.requirements_text, str) else None,
                     benefits, contract, hours, soft, langs,
                     "vietjobs", "active", posted))
        for pos, s in enumerate(r.skills):
            job_skills_rows.append((key, s, 1.0 if pos < 5 else 0.5))

    execute_values(cur, """INSERT INTO job_posting (job_key, company_id, title, category, location, level,
        exp_years_min, education, salary_min, salary_max, description, requirements,
        benefits, contract_type, working_hours, soft_skills, languages_required,
        source, status, posted_at)
        VALUES %s ON CONFLICT (job_key) DO UPDATE SET
            benefits = EXCLUDED.benefits,
            contract_type = EXCLUDED.contract_type,
            working_hours = EXCLUDED.working_hours,
            soft_skills = EXCLUDED.soft_skills,
            languages_required = EXCLUDED.languages_required
    """, rows, page_size=500)

    cur.execute("SELECT job_key, id FROM job_posting")
    jid = dict(cur.fetchall())
    execute_values(cur, "INSERT INTO job_skill (job_id, skill_id, weight) VALUES %s ON CONFLICT DO NOTHING",
                   [(jid[k], skill_id[s], w) for k, s, w in job_skills_rows], page_size=1000)
    conn.commit()
    cur.execute("SELECT COUNT(*), COUNT(benefits), COUNT(working_hours), COUNT(languages_required) FROM job_posting")
    print("job_posting stats (total, has_benefits, has_hours, has_langs):", cur.fetchone())
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
