"""Matching Score engine: 6 features in [0,1] + two scorers (heuristic-v1, lr-v1).

Features: skill_cov, text_sim (TF-IDF word 1-2gram + char 3-5gram), exp_fit, edu_fit, loc_fit, salary_fit.
Everything is vectorised over (candidate, job) pairs, so scoring one candidate against all jobs is one call.
"""
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

from app.db import connect
from etl.common import EDU_RANK

MODELS = Path(__file__).resolve().parents[1] / "models"
FEATURES = ["skill_cov", "text_sim", "exp_fit", "edu_fit", "loc_fit", "salary_fit", "level_fit"]
HEURISTIC_W = np.array([0.42, 0.18, 0.10, 0.07, 0.07, 0.06, 0.10])
LEVEL_RANK = {"Intern": 0, "Junior": 1, "Mid": 2, "Senior": 3, "Manager": 4}
LEVEL_TYPICAL_EXP = {"Intern": 0.0, "Junior": 1.0, "Mid": 3.0, "Senior": 6.0, "Manager": 8.0}


def candidate_level(exp: float) -> int:
    """Seniority implied by years of experience (same cut-offs as etl.common.infer_level without a title)."""
    return 3 if exp >= 5 else (2 if exp >= 2 else 1)
HIGH, MID = 0.75, 0.55
_LOCK = threading.Lock()
_ENGINE: Optional["Engine"] = None


def band(score: float) -> str:
    return "cao" if score >= HIGH else ("trung bình" if score >= MID else "thấp")


def job_text(title, description, requirements) -> str:
    return f"{title or ''} {(description or '')[:800]} {(requirements or '')[:400]}"


def candidate_text(profile: Dict) -> str:
    return " ".join(sorted(profile["skills"])) + " " + (profile.get("major") or "")


class Engine:
    def __init__(self):
        conn = connect(retries=3)
        cur = conn.cursor()
        cur.execute("""SELECT id, title, category, location, level, exp_years_min, education, salary_min,
                       salary_max, description, requirements, company_id FROM job_posting
                       WHERE status='active' ORDER BY id""")
        rows = cur.fetchall()
        cur.execute("SELECT id, name FROM skill ORDER BY id")
        sk = cur.fetchall()
        cur.execute("SELECT job_id, skill_id, weight FROM job_skill")
        js = cur.fetchall()
        conn.close()
        self.skill_names = [n for _, n in sk]
        self.skill_idx = {n: i for i, (_, n) in enumerate(sk)}
        sid_idx = {sid: i for i, (sid, _) in enumerate(sk)}
        self.job_ids = np.array([r[0] for r in rows])
        self.job_pos = {int(j): i for i, j in enumerate(self.job_ids)}
        self.title = [r[1] for r in rows]
        self.category = [r[2] for r in rows]
        self.location = [r[3] for r in rows]
        self.level = [r[4] for r in rows]
        self.level_rank = np.array([LEVEL_RANK.get(r[4], 1) for r in rows])
        self.exp_min = np.array([float(r[5] or 0) for r in rows])
        self.edu_rank = np.array([EDU_RANK.get(r[6], 0) for r in rows])
        self.sal_max = np.array([float(r[8]) if r[8] is not None else np.nan for r in rows])
        self.company_id = [r[11] for r in rows]
        texts = [job_text(r[1], r[9], r[10]) for r in rows]
        i_arr, j_arr, w_arr = [], [], []
        for jid, sid, w in js:
            if int(jid) in self.job_pos:
                i_arr.append(self.job_pos[int(jid)])
                j_arr.append(sid_idx[sid])
                w_arr.append(float(w))
        self.W = sp.csr_matrix((w_arr, (i_arr, j_arr)), shape=(len(rows), len(sk)))
        self.vec_w, self.vec_c = self._vectorizers(texts)
        self.Xw, self.Xc = self.vec_w.transform(texts), self.vec_c.transform(texts)
        self.meta = json.loads((MODELS / "meta.json").read_text(encoding="utf-8")) if (MODELS / "meta.json").exists() else {}
        lr_path = MODELS / "lr.joblib"
        self.lr = joblib.load(lr_path) if lr_path.exists() else None
        self.default_model = self.meta.get("default", "lr-v1") if self.lr is not None else "heuristic-v1"

    @staticmethod
    def _vectorizers(texts):
        path = MODELS / "tfidf.joblib"
        if path.exists():
            return joblib.load(path)
        vw = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True)
        vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=60000, sublinear_tf=True)
        vw.fit(texts)
        vc.fit(texts)
        MODELS.mkdir(exist_ok=True)
        joblib.dump((vw, vc), path)
        return vw, vc

    # ------------------------------------------------------------ features
    def features(self, profiles: List[Dict], cand_idx: np.ndarray, job_idx: np.ndarray) -> np.ndarray:
        """Pairwise feature matrix (n_pairs x 6). cand_idx indexes `profiles`, job_idx indexes engine jobs."""
        m, n = len(profiles), len(job_idx)
        rows, cols = [], []
        for i, p in enumerate(profiles):
            for s in p["skills"]:
                if s in self.skill_idx:
                    rows.append(i)
                    cols.append(self.skill_idx[s])
        C = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(m, len(self.skill_names)))[cand_idx]
        Wj = self.W[job_idx]
        den = np.asarray(Wj.sum(1)).ravel()
        num = np.asarray(Wj.multiply(C).sum(1)).ravel()
        cov = np.where(den > 0, num / np.maximum(den, 1e-9), 0.5)

        texts = [candidate_text(p) for p in profiles]
        Pw, Pc = self.vec_w.transform(texts)[cand_idx], self.vec_c.transform(texts)[cand_idx]
        sim = 0.5 * (np.asarray(Pw.multiply(self.Xw[job_idx]).sum(1)).ravel()
                     + np.asarray(Pc.multiply(self.Xc[job_idx]).sum(1)).ravel())

        exp_c = np.array([float(p.get("exp") or 0) for p in profiles])[cand_idx]
        req = self.exp_min[job_idx]
        exp_fit = np.where(req <= 0, 1.0, np.minimum(exp_c / np.maximum(req, 1e-9), 1.0))

        rc = np.array([EDU_RANK.get(p.get("edu"), 0) for p in profiles])[cand_idx]
        rj = self.edu_rank[job_idx]
        edu_fit = np.where((rj == 0) | (rc >= rj), 1.0, rc / np.maximum(rj, 1))

        loc_c = np.array([p.get("location") or "" for p in profiles], dtype=object)[cand_idx]
        loc_j = np.array(self.location, dtype=object)[job_idx]
        loc_fit = np.where(loc_c == "", 0.5, np.where(loc_c == loc_j, 1.0, np.where(loc_j == "Khác", 0.5, 0.3)))

        sal_c = np.array([float(p["salary"]) if p.get("salary") else np.nan for p in profiles])[cand_idx]
        smax = self.sal_max[job_idx]
        sal_fit = np.where(np.isnan(sal_c) | np.isnan(smax), 0.5, np.where(sal_c <= smax, 1.0, smax / np.maximum(sal_c, 1e-9)))
        # level_fit is two-sided: both under- and over-qualified candidates lose points
        lvl_c = np.array([candidate_level(float(p.get("exp") or 0)) for p in profiles])[cand_idx]
        lvl_j = self.level_rank[job_idx]
        level_fit = np.maximum(0.0, 1.0 - 0.4 * np.abs(lvl_c - lvl_j))
        return np.clip(np.column_stack([cov, sim, exp_fit, edu_fit, loc_fit, sal_fit, level_fit]), 0, 1)

    def predict(self, F: np.ndarray, model: Optional[str] = None) -> np.ndarray:
        model = model or self.default_model
        if model == "lr-v1" and self.lr is not None:
            return self.lr.predict_proba(F)[:, 1]
        return F @ HEURISTIC_W

    # ------------------------------------------------------------ one candidate
    def score_all(self, profile: Dict, model: Optional[str] = None):
        n = len(self.job_ids)
        F = self.features([profile], np.zeros(n, dtype=int), np.arange(n))
        return self.predict(F, model), F

    def score_jobs(self, profile: Dict, job_ids: List[int], model: Optional[str] = None) -> Dict[int, float]:
        pos = [self.job_pos[j] for j in job_ids if j in self.job_pos]
        if not pos:
            return {}
        F = self.features([profile], np.zeros(len(pos), dtype=int), np.array(pos))
        s = self.predict(F, model)
        return {int(self.job_ids[p]): float(v) for p, v in zip(pos, s)}

    def job_skills(self, pos: int) -> Dict[str, float]:
        row = self.W[pos]
        return {self.skill_names[c]: float(w) for c, w in zip(row.indices, row.data)}

    def category_popularity(self, category: str) -> Dict[str, int]:
        idx = [i for i, c in enumerate(self.category) if c == category]
        cnt = np.asarray((self.W[idx] > 0).sum(0)).ravel()
        return {self.skill_names[c]: int(cnt[c]) for c in np.nonzero(cnt)[0]}

    def explain(self, profile: Dict, job_id: int, model: Optional[str] = None) -> Dict:
        pos = self.job_pos[int(job_id)]
        F = self.features([profile], np.zeros(1, dtype=int), np.array([pos]))
        score = float(self.predict(F, model)[0])
        comps = {k: round(float(v), 3) for k, v in zip(FEATURES, F[0])}
        req = self.job_skills(pos)
        have = {s.lower() for s in profile["skills"]}
        matched = sorted((s for s in req if s.lower() in have), key=lambda s: -req[s])
        pop = self.category_popularity(self.category[pos])
        missing = sorted((s for s in req if s.lower() not in have), key=lambda s: (-req[s], -pop.get(s, 0)))
        parts = [f"Khớp {len(matched)}/{len(req)} kỹ năng yêu cầu"
                 + (f" ({', '.join(matched[:3])})" if matched else "")]
        if missing:
            parts.append("còn thiếu " + ", ".join(missing[:3]))
        if comps["exp_fit"] < 0.7:
            parts.append(f"kinh nghiệm thấp hơn yêu cầu ({self.exp_min[pos]:g} năm)")
        if comps["level_fit"] < 0.7:
            parts.append(f"cấp bậc khác vị trí ({self.level[pos]})")
        if comps["loc_fit"] >= 1:
            parts.append("cùng địa điểm")
        elif comps["loc_fit"] < 0.5:
            parts.append(f"khác địa điểm ({self.location[pos]})")
        return {"job_id": int(job_id), "score": round(score, 4), "level": band(score), "components": comps,
                "matched_skills": matched, "missing_skills": missing, "explanation": "; ".join(parts) + ".",
                "model_version": model or self.default_model}


def get_engine(refresh: bool = False) -> Engine:
    global _ENGINE
    with _LOCK:
        if _ENGINE is None or refresh:
            _ENGINE = Engine()
        return _ENGINE


def invalidate():
    global _ENGINE
    with _LOCK:
        _ENGINE = None


def load_profile(cur, candidate_id: int) -> Dict:
    cur = cur.connection.cursor()  # callers may pass a dict cursor
    cur.execute("""SELECT full_name, major, exp_years, education, location, expected_salary
                   FROM candidate WHERE id=%s""", (candidate_id,))
    r = cur.fetchone()
    cur.execute("""SELECT s.name FROM candidate_skill cs JOIN skill s ON s.id=cs.skill_id
                   WHERE cs.candidate_id=%s""", (candidate_id,))
    return {"id": candidate_id, "name": r[0], "major": r[1], "exp": float(r[2] or 0), "edu": r[3],
            "location": r[4], "salary": float(r[5]) if r[5] is not None else None,
            "skills": {x[0] for x in cur.fetchall()}}


def refresh_matches(conn, candidate_id: int, top: int = 100, model: Optional[str] = None) -> int:
    """Batch-score one candidate against all jobs and persist the top-N into matching_result."""
    eng = get_engine()
    cur = conn.cursor()
    prof = load_profile(cur, candidate_id)
    scores, F = eng.score_all(prof, model)
    version = model or eng.default_model
    order = np.argsort(-scores)[:top]
    cur.execute("DELETE FROM matching_result WHERE candidate_id=%s AND model_version=%s", (candidate_id, version))
    have = {s.lower() for s in prof["skills"]}
    for p in order:
        req = eng.job_skills(int(p))
        matched = [s for s in req if s.lower() in have]
        missing = [s for s in req if s.lower() not in have]
        cur.execute("""INSERT INTO matching_result (candidate_id, job_id, score, components_json, matched_skills,
                       missing_skills, model_version) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (candidate_id, int(eng.job_ids[p]), float(round(scores[p], 4)),
                     json.dumps({k: round(float(v), 3) for k, v in zip(FEATURES, F[p])}), matched, missing, version))
    conn.commit()
    return len(order)
