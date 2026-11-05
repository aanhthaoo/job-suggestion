"""Train lr-v1 on weak labels. Run: python -m ml.train_match

Weak labels (anti-circularity): positives are noisy candidates derived from a job (50-80% of its skills,
1-3 noise skills, experience +-1y). Hard negatives: same category but different level or <30% skill overlap.
Easy negatives: other categories. Train/test split BY CATEGORY (held-out industries are never seen in training).
"""
import json
import random
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from etl.common import EDU_RANK
from ml.matching import FEATURES, HEURISTIC_W, LEVEL_TYPICAL_EXP, MODELS, Engine
from etl.common import MAIN_LOCATIONS

TEST_CATEGORIES = ["Công nghệ thông tin", "Tài chính - Kế toán", "Logistics - Vận tải", "Xây dựng - Kiến trúc"]
SEED = 42
EDU_BY_RANK = {v: k for k, v in EDU_RANK.items()}


def gen_candidate(rng: random.Random, eng: Engine, pos: int) -> dict:
    req = eng.job_skills(pos)
    names = list(req)
    k = max(1, round(len(names) * rng.uniform(0.5, 0.8)))
    skills = set(rng.sample(names, min(k, len(names))))
    skills |= set(rng.sample(eng.skill_names, rng.randint(1, 3)))
    edu_rank = min(5, int(eng.edu_rank[pos]) + rng.choice([0, 0, 1]))
    sal = None
    if not np.isnan(eng.sal_max[pos]):
        sal = round(float(eng.sal_max[pos]) * rng.uniform(0.6, 1.1), 1)
    # experience follows the job's seniority (typical years for its level, never below its minimum), +-1 year
    base = max(float(eng.exp_min[pos]), LEVEL_TYPICAL_EXP.get(eng.level[pos], 1.0))
    return {"skills": skills, "exp": max(0.0, base + rng.choice([-1, 0, 1])),
            "edu": EDU_BY_RANK[edu_rank], "salary": sal, "major": eng.category[pos],
            "location": eng.location[pos] if rng.random() < 0.7 else rng.choice(MAIN_LOCATIONS)}


def build_pairs(eng: Engine, positions, rng: random.Random):
    profiles, cidx, jidx, y = [], [], [], []
    by_cat = {}
    for i, c in enumerate(eng.category):
        by_cat.setdefault(c, []).append(i)
    sets = [set(eng.job_skills(i)) for i in range(len(eng.job_ids))]
    for pos in positions:
        prof = gen_candidate(rng, eng, pos)
        ci = len(profiles)
        profiles.append(prof)
        cidx.append(ci), jidx.append(pos), y.append(1)
        for _ in range(30):  # hard negative
            j = rng.choice(by_cat[eng.category[pos]])
            if j == pos:
                continue
            overlap = len(sets[j] & sets[pos]) / max(1, len(sets[j] | sets[pos]))
            if eng.level[j] != eng.level[pos] or overlap < 0.3:
                cidx.append(ci), jidx.append(j), y.append(0)
                break
        other = [c for c in by_cat if c != eng.category[pos]]
        cidx.append(ci), jidx.append(rng.choice(by_cat[rng.choice(other)])), y.append(0)
    return profiles, np.array(cidx), np.array(jidx), np.array(y)


def main():
    rng = random.Random(SEED)
    for f in ("lr.joblib", "meta.json"):  # train features must not depend on an older model
        (MODELS / f).unlink(missing_ok=True)
    eng = Engine()
    train_pos = [i for i, c in enumerate(eng.category) if c not in TEST_CATEGORIES]
    test_pos = [i for i, c in enumerate(eng.category) if c in TEST_CATEGORIES]
    P, c, j, y = build_pairs(eng, train_pos, rng)
    F = eng.features(P, c, j)
    lr = LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000).fit(F, y)
    P2, c2, j2, y2 = build_pairs(eng, test_pos, random.Random(SEED + 1))
    F2 = eng.features(P2, c2, j2)
    auc_lr = roc_auc_score(y2, lr.predict_proba(F2)[:, 1])
    auc_h = roc_auc_score(y2, F2 @ HEURISTIC_W)
    auc_cov = roc_auc_score(y2, F2[:, 0])
    MODELS.mkdir(exist_ok=True)
    import joblib
    joblib.dump(lr, MODELS / "lr.joblib")
    meta = {"default": "lr-v1" if auc_lr >= auc_h else "heuristic-v1",
            "test_categories": TEST_CATEGORIES, "train_pairs": int(len(y)), "test_pairs": int(len(y2)),
            "auc_test": {"lr-v1": round(auc_lr, 4), "heuristic-v1": round(auc_h, 4), "skill_cov": round(auc_cov, 4)},
            "coef": {k: round(float(v), 3) for k, v in zip(FEATURES, lr.coef_[0])},
            "intercept": round(float(lr.intercept_[0]), 3)}
    (MODELS / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
