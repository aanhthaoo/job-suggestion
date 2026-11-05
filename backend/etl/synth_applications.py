"""Simulated applications + funnel outcomes (is_simulated=true).

P(reach next stage) = sigmoid(a*score + b_stage + job_difficulty + candidate_quality + noise), seed 42.
job_difficulty (competition for that posting) and candidate_quality (unobserved) are independent of the match score,
so the score is a useful but imperfect predictor and calibration is not guaranteed by construction. Initially score=skill_cov;
re-run after Phase 5 with the real matching model: python -m etl.synth_applications --rebuild --engine
"""
import math
import random
import sys
from collections import defaultdict
from datetime import timedelta
from psycopg2.extras import execute_values
from app.db import connect

SEED = 42
A = 3.5
B = [-2.2, -2.6, -2.9]  # screening, interview, offer (conditional on previous stage)


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def skill_cov(cand: set, job: dict) -> float:
    tot = sum(job.values()) or 1.0
    return sum(w for s, w in job.items() if s in cand) / tot


def main(score_fn=None, rebuild=False, use_engine=False):
    rng = random.Random(SEED)
    conn = connect()
    cur = conn.cursor()
    if rebuild:
        cur.execute("DELETE FROM application WHERE is_simulated")
    cur.execute("SELECT COUNT(*) FROM application WHERE is_simulated")
    if cur.fetchone()[0] > 0:
        print("applications already seeded (use --rebuild)")
        return
    cur.execute("SELECT id, category, posted_at FROM job_posting WHERE status='active'")
    jobs = cur.fetchall()
    by_cat = defaultdict(list)
    for jid, cat, posted in jobs:
        by_cat[cat].append((jid, posted))
    all_pool = [(j, p) for j, _, p in jobs]
    job_sk = defaultdict(dict)
    cur.execute("SELECT job_id, skill_id, weight FROM job_skill")
    for j, s, w in cur.fetchall():
        job_sk[j][s] = float(w)
    cand_sk = defaultdict(set)
    cur.execute("SELECT candidate_id, skill_id FROM candidate_skill")
    for c, s in cur.fetchall():
        cand_sk[c].add(s)
    cur.execute("SELECT id, major FROM candidate WHERE is_simulated ORDER BY id")
    cands = cur.fetchall()
    fn = score_fn or (lambda cid, jid: skill_cov(cand_sk[cid], job_sk[jid]))
    if use_engine:
        from ml.matching import get_engine, load_profile
        eng = get_engine(refresh=True)
        cache = {}

        def fn(cid, jid):  # one batched scoring call per candidate, then dict lookups
            if cid not in cache:
                cache[cid] = eng.score_jobs(load_profile(cur, cid), [int(x) for x in eng.job_ids])
            return cache[cid].get(jid, 0.0)

    job_diff = {j: random.Random(f"job{j}").gauss(0, 0.8) for j, _ in all_pool}
    rows = []
    for cid, major in cands:
        quality = random.Random(f"cand{cid}").gauss(0, 0.5)
        pool = by_cat.get(major) or all_pool
        scored = sorted(((fn(cid, j), j, p) for j, p in pool), reverse=True)
        top = scored[:25]
        n_apply = min(rng.randint(4, 9), len(pool))
        picked = {}
        while len(picked) < n_apply:
            if rng.random() < 0.6 and top:
                s, j, p = rng.choice(top)
                src = "recommend"
            else:
                j, p = rng.choice(pool)
                s, src = fn(cid, j), "search"
            picked[j] = (s, p, src)
        for j, (s, p, src) in picked.items():
            stage = 0
            for b in B:
                if rng.random() < sigmoid(A * s + b + job_diff[j] + quality + rng.gauss(0, 0.3)):
                    stage += 1
                else:
                    break
            if stage == 3:
                status = "offer"
            elif stage > 0 and rng.random() < 0.35:
                status = ("screening", "interview")[stage - 1]  # still in progress
            elif stage == 0 and rng.random() < 0.25:
                status = "applied"
            else:
                status = "rejected"
            applied = p + timedelta(days=rng.randint(0, 20)) if p else None
            rows.append((cid, j, status, stage, round(s, 4), src, applied,
                         (applied + timedelta(days=rng.randint(1, 14))) if applied else None, True))
    execute_values(cur, """INSERT INTO application (candidate_id, job_id, status, stage_reached, match_score,
                           source, applied_at, updated_at, is_simulated) VALUES %s ON CONFLICT DO NOTHING""", rows)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM application")
    print("applications:", cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main(rebuild="--rebuild" in sys.argv, use_engine="--engine" in sys.argv)
