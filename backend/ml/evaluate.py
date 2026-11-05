"""Offline evaluation -> reports/metrics.json. Run: python -m ml.evaluate

Ranking task on HELD-OUT industries (never used to train lr-v1): each test candidate is a noisy profile derived from
a source job (50-80% of its skills + noise). Relevant = jobs of the same category and level, |exp diff| <= 1, whose
skill-set Jaccard with the source job >= 0.4 (job-job relation, independent of the candidate's noisy sample).
Known limitation: labels are synthetic; the human-label file (reports/label_me.csv) is the external check.
"""
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from ml.matching import HEURISTIC_W, Engine, get_engine
from ml.train_match import TEST_CATEGORIES, gen_candidate
from scipy.stats import spearmanr

REPORTS = Path(__file__).resolve().parents[2] / "reports"
SEED = 42
N_CAND = 400
METHODS = ["random", "tfidf_only", "skill_cov_only", "heuristic-v1", "lr-v1"]


def relevant_set(eng: Engine, src: int, pool: np.ndarray, sets) -> set:
    rel = set()
    for j in pool:
        if eng.category[j] != eng.category[src] or eng.level[j] != eng.level[src]:
            continue
        if abs(eng.exp_min[j] - eng.exp_min[src]) > 1:
            continue
        if j == src or len(sets[j] & sets[src]) / max(1, len(sets[j] | sets[src])) >= 0.4:
            rel.add(int(j))
    return rel


def metrics_for(ranked: np.ndarray, rel: set):
    top5, top10 = ranked[:5], ranked[:10]
    p5 = sum(int(j) in rel for j in top5) / 5
    rec10 = sum(int(j) in rel for j in top10) / max(1, min(len(rel), 10))
    mrr = next((1 / (r + 1) for r, j in enumerate(ranked) if int(j) in rel), 0.0)
    dcg = sum(1 / np.log2(r + 2) for r, j in enumerate(top10) if int(j) in rel)
    idcg = sum(1 / np.log2(r + 2) for r in range(min(len(rel), 10)))
    return p5, rec10, mrr, dcg / idcg if idcg else 0.0


def bootstrap_ci(values: np.ndarray, rng, n=1000):
    means = [values[rng.integers(0, len(values), len(values))].mean() for _ in range(n)]
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def ranking_eval(eng: Engine):
    rng_py, rng = random.Random(SEED), np.random.default_rng(SEED)
    pool = np.array([i for i, c in enumerate(eng.category) if c in TEST_CATEGORIES])
    sets = [set(eng.job_skills(i)) for i in range(len(eng.job_ids))]
    sources = rng_py.sample(list(pool), min(N_CAND, len(pool)))
    profiles = [gen_candidate(rng_py, eng, s) for s in sources]
    per = {m: [] for m in METHODS}
    rel_sizes = []
    for ci, (prof, src) in enumerate(zip(profiles, sources)):
        F = eng.features([prof], np.zeros(len(pool), dtype=int), pool)
        rel = relevant_set(eng, src, pool, sets)
        rel_sizes.append(len(rel))
        scores = {"random": rng.random(len(pool)), "tfidf_only": F[:, 1], "skill_cov_only": F[:, 0],
                  "heuristic-v1": F @ HEURISTIC_W, "lr-v1": eng.predict(F, "lr-v1")}
        for m in METHODS:
            order = pool[np.argsort(-scores[m], kind="stable")]
            per[m].append(metrics_for(order, rel))
    out = {}
    names = ["P@5", "Recall@10", "MRR", "nDCG@10"]
    for m in METHODS:
        arr = np.array(per[m])
        out[m] = {n: {"mean": round(float(arr[:, k].mean()), 4), "ci95": bootstrap_ci(arr[:, k], rng)}
                  for k, n in enumerate(names)}
    return out, {"n_candidates": len(sources), "pool_size": int(len(pool)), "mean_relevant": round(float(np.mean(rel_sizes)), 1)}, \
        (profiles, sources, pool)


def sensitivity(eng: Engine, profiles, sources, n=200):
    rng = random.Random(SEED)
    up, down, d_up, d_down = 0, 0, [], []
    for prof, src in rng.sample(list(zip(profiles, sources)), min(n, len(profiles))):
        jid = int(eng.job_ids[src])
        base = eng.score_jobs(prof, [jid], "lr-v1")[jid]
        req = eng.job_skills(src)
        miss = [s for s in req if s not in prof["skills"]]
        have = [s for s in req if s in prof["skills"]]
        if miss:
            s2 = eng.score_jobs({**prof, "skills": prof["skills"] | {miss[0]}}, [jid], "lr-v1")[jid]
            d_up.append(s2 - base)
            up += s2 >= base
        if have:
            s3 = eng.score_jobs({**prof, "skills": prof["skills"] - {have[0]}}, [jid], "lr-v1")[jid]
            d_down.append(s3 - base)
            down += s3 <= base
    return {"add_required_skill": {"mean_delta": round(float(np.mean(d_up)), 4), "pct_non_decreasing": round(up / max(1, len(d_up)), 3), "n": len(d_up)},
            "remove_matched_skill": {"mean_delta": round(float(np.mean(d_down)), 4), "pct_non_increasing": round(down / max(1, len(d_down)), 3), "n": len(d_down)}}


def latency(n=100):
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    tok = c.post("/api/v1/auth/login", json={"email": "candidate@demo.com", "password": "demo123"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    top = c.get("/api/v1/recommendations?k=1", headers=h).json()["recommendations"][0]["job"]["id"]
    res = {}
    for name, url in (("GET /recommendations?k=20", "/api/v1/recommendations?k=20"), ("GET /jobs/{id}/match", f"/api/v1/jobs/{top}/match"),
                      ("GET /jobs (with match_score)", "/api/v1/jobs?limit=10")):
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            assert c.get(url, headers=h).status_code == 200
            ts.append((time.perf_counter() - t) * 1000)
        res[name] = {"p50_ms": round(float(np.percentile(ts, 50)), 1), "p95_ms": round(float(np.percentile(ts, 95)), 1), "n": n}
    return res


def error_examples(eng: Engine, profiles, sources, pool, k=3):
    """First k candidates whose lr-v1 top-1 job is not relevant (for the written error analysis)."""
    sets = [set(eng.job_skills(i)) for i in range(len(eng.job_ids))]
    out = []
    for prof, src in zip(profiles, sources):
        F = eng.features([prof], np.zeros(len(pool), dtype=int), pool)
        s = eng.predict(F, "lr-v1")
        best = int(pool[int(np.argmax(s))])
        if best in relevant_set(eng, src, pool, sets):
            continue
        jid = int(eng.job_ids[best])
        ex = eng.explain(prof, jid, "lr-v1")
        out.append({"source_job": f"{eng.title[src]} ({eng.category[src]}, {eng.level[src]})",
                    "candidate_skills": sorted(prof["skills"]), "top1_job": f"{eng.title[best]} ({eng.category[best]}, {eng.level[best]})",
                    "top1_score": ex["score"], "matched": ex["matched_skills"], "why_wrong": (
                        "khác ngành (mô hình chưa có đặc trưng khớp ngành, chỉ dựa vào kỹ năng chung)" if eng.category[best] != eng.category[src] else
                        "khác cấp bậc" if eng.level[best] != eng.level[src] else
                        "kinh nghiệm yêu cầu lệch >1 năm" if abs(eng.exp_min[best] - eng.exp_min[src]) > 1 else
                        "trùng kỹ năng chung nhưng bộ kỹ năng vai trò khác (Jaccard thấp)")})
        if len(out) == k:
            break
    return out


def outcome_by_band():
    from app.db import connect
    conn = connect(retries=2)
    cur = conn.cursor()
    cur.execute("SELECT score_band, n_applications, interview_rate, offer_rate FROM v_match_vs_outcome")
    rows = {r[0]: {"n": r[1], "interview_rate": float(r[2]), "offer_rate": float(r[3])} for r in cur.fetchall()}
    conn.close()
    return rows


def label_file(eng: Engine, profiles, sources, pool):
    """20 (candidate, job) pairs for a human to rate 1-5. Model scores go to a separate key file (no anchoring)."""
    REPORTS.mkdir(exist_ok=True)
    rng = random.Random(SEED + 7)
    idx = rng.sample(range(len(profiles)), 10)
    rows, key = [], []
    for k, i in enumerate(idx):
        prof = profiles[i]
        F = eng.features([prof], np.zeros(len(pool), dtype=int), pool)
        s = eng.predict(F, "lr-v1")
        order = np.argsort(-s)
        for tag, pos in (("top", order[0]), ("mid", order[len(order) // 3])):
            j = int(pool[pos])
            pid = f"P{len(rows) + 1:02d}"
            rows.append({"pair_id": pid, "candidate_major": prof["major"], "candidate_skills": "; ".join(sorted(prof["skills"])),
                         "candidate_exp_years": prof["exp"], "candidate_education": prof["edu"],
                         "candidate_location": prof["location"], "candidate_expected_salary_trieu": prof["salary"] or "",
                         "job_title": eng.title[j], "job_category": eng.category[j], "job_level": eng.level[j],
                         "job_skills": "; ".join(eng.job_skills(j)), "job_exp_min": eng.exp_min[j],
                         "job_location": eng.location[j], "job_salary_max_trieu": "" if np.isnan(eng.sal_max[j]) else eng.sal_max[j],
                         "human_score_1_to_5": ""})
            key.append({"pair_id": pid, "model_score": round(float(s[pos]), 4), "slot": tag})
    path = REPORTS / "label_me.csv"
    if not path.exists() or "--relabel" in sys.argv:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        with open(REPORTS / "label_me_key.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["pair_id", "model_score", "slot"])
            w.writeheader()
            w.writerows(key)
    return spearman_from_labels()


def _read_rater(path):
    with open(path, encoding="utf-8-sig") as f:
        out = {}
        for r in csv.DictReader(f):
            v = (r.get("human_score_1_to_5") or "").strip().replace(",", ".")
            if v:
                try:
                    x = float(v)
                except ValueError:
                    continue
                if 1 <= x <= 5:
                    out[r["pair_id"]] = x
        return out


def spearman_from_labels():
    """Raters = reports/label_me.csv plus any reports/label_me_<name>.csv. Scores are averaged per pair."""
    kp = REPORTS / "label_me_key.csv"
    files = sorted(p for p in REPORTS.glob("label_me*.csv") if p.name != "label_me_key.csv")
    if not (files and kp.exists()):
        return {"status": "no_labels"}
    with open(kp, encoding="utf-8") as f:
        model = {r["pair_id"]: float(r["model_score"]) for r in csv.DictReader(f)}
    raters = {p.stem: _read_rater(p) for p in files}
    raters = {k: v for k, v in raters.items() if v}
    n_lab = max((len(v) for v in raters.values()), default=0)
    if n_lab < 10:
        return {"status": "not_validated_by_humans", "n_labeled": n_lab, "n_raters": len(raters),
                "note": "Điền cột human_score_1_to_5 (>=10 dòng, thang 1-5) trong reports/label_me.csv rồi chạy lại ml.evaluate"}
    pairs = sorted(set().union(*[set(v) for v in raters.values()]) & set(model))
    mean_h = [float(np.mean([v[p] for v in raters.values() if p in v])) for p in pairs]
    rho, pv = spearmanr(mean_h, [model[p] for p in pairs])
    out = {"status": "validated", "n_labeled": len(pairs), "n_raters": len(raters), "spearman_rho": round(float(rho), 3),
           "p_value": round(float(pv), 4)}
    names = list(raters)
    if len(names) >= 2:
        rhos = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                common = sorted(set(raters[names[i]]) & set(raters[names[j]]))
                if len(common) >= 5:
                    rhos.append(float(spearmanr([raters[names[i]][p] for p in common], [raters[names[j]][p] for p in common])[0]))
        if rhos:
            out["inter_rater_spearman_mean"] = round(float(np.mean(rhos)), 3)
    return out


def main():
    eng = get_engine(refresh=True)
    ranking, setup, (profiles, sources, pool) = ranking_eval(eng)
    meta = json.loads((Path(__file__).parents[1] / "models" / "meta.json").read_text(encoding="utf-8"))
    sal = json.loads((Path(__file__).parents[1] / "models" / "salary_metrics.json").read_text(encoding="utf-8"))
    out = {
        "setup": {**setup, "test_categories": TEST_CATEGORIES, "seed": SEED, "default_model": eng.default_model,
                  "relevance": "same category+level, |exp diff|<=1, job-job skill Jaccard>=0.4 (synthetic labels)"},
        "classification_auc_test": meta["auc_test"], "lr_coefficients": meta["coef"],
        "ranking": ranking, "sensitivity_lr": sensitivity(eng, profiles, sources),
        "latency": latency(), "salary_model": sal, "outcome_by_score_band_simulated": outcome_by_band(),
        "human_labels": label_file(eng, profiles, sources, pool),
        "error_examples": error_examples(eng, profiles, sources, pool),
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "metrics.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ranking": {m: {k: v["mean"] for k, v in d.items()} for m, d in ranking.items()},
                      "latency": out["latency"], "human": out["human_labels"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
