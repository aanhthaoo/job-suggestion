"""Matching features, determinism, sensitivity, and the learned model."""
import numpy as np
import pytest

from ml.matching import FEATURES, HEURISTIC_W, band, get_engine

PROFILE = {"skills": {"Python", "SQL", "Excel"}, "exp": 2.0, "edu": "Đại học", "location": "Hà Nội",
           "salary": 12.0, "major": "Công nghệ thông tin"}


@pytest.fixture(scope="module")
def eng():
    return get_engine()


def _pick_job(eng):
    """A job requiring >=3 skills."""
    for i in range(len(eng.job_ids)):
        if len(eng.job_skills(i)) >= 3:
            return i
    raise AssertionError("no suitable job")


def test_features_in_unit_range(eng):
    n = 200
    F = eng.features([PROFILE], np.zeros(n, dtype=int), np.arange(n))
    assert F.shape == (n, len(FEATURES)) and F.min() >= 0 and F.max() <= 1


def test_skill_cov_exact(eng):
    pos = _pick_job(eng)
    req = eng.job_skills(pos)
    full = {"skills": set(req), "exp": 99, "edu": "Thạc sĩ", "location": "Hà Nội", "salary": None, "major": ""}
    none = {**full, "skills": set()}
    f_full = eng.features([full], np.array([0]), np.array([pos]))[0]
    f_none = eng.features([none], np.array([0]), np.array([pos]))[0]
    assert f_full[0] == pytest.approx(1.0) and f_none[0] == 0.0
    assert f_full[2] == 1.0 and f_full[3] == 1.0


def test_exp_edu_loc_salary_fit(eng):
    pos = _pick_job(eng)
    base = {"skills": set(), "exp": 0, "edu": "Thạc sĩ", "location": eng.location[pos], "salary": None, "major": ""}
    hi = eng.features([{**base, "exp": 50}], np.array([0]), np.array([pos]))[0]
    lo = eng.features([{**base, "exp": 0}], np.array([0]), np.array([pos]))[0]
    assert hi[2] >= lo[2]
    assert hi[4] == 1.0  # same location
    far = eng.features([{**base, "location": "Nowhere"}], np.array([0]), np.array([pos]))[0]
    assert far[4] < 1.0
    rich = eng.features([{**base, "salary": 10_000.0}], np.array([0]), np.array([pos]))[0]
    assert rich[5] <= 0.5 or np.isnan(eng.sal_max[pos])


def test_deterministic(eng):
    a, _ = eng.score_all(PROFILE)
    b, _ = eng.score_all(dict(PROFILE, skills=set(PROFILE["skills"])))
    assert np.array_equal(a, b)
    assert eng.explain(PROFILE, int(eng.job_ids[0])) == eng.explain(PROFILE, int(eng.job_ids[0]))


def test_sensitivity_adding_required_skill_never_lowers_score(eng):
    pos = _pick_job(eng)
    jid = int(eng.job_ids[pos])
    req = eng.job_skills(pos)
    p0 = {**PROFILE, "skills": set()}
    s_prev = eng.score_jobs(p0, [jid])[jid]
    skills = set()
    for s in req:
        skills.add(s)
        s_new = eng.score_jobs({**PROFILE, "skills": set(skills)}, [jid])[jid]
        assert s_new >= s_prev - 1e-9
        s_prev = s_new


def test_explain_structure(eng):
    pos = _pick_job(eng)
    ex = eng.explain({**PROFILE, "skills": {"Python"}}, int(eng.job_ids[pos]))
    assert set(ex["components"]) == set(FEATURES)
    assert ex["level"] in ("cao", "trung bình", "thấp") and ex["explanation"].startswith("Khớp")
    assert set(ex["matched_skills"]).isdisjoint(ex["missing_skills"])


def test_band_thresholds():
    assert band(0.75) == "cao" and band(0.60) == "trung bình" and band(0.54) == "thấp"


def test_learned_model_present_and_separates(eng):
    assert eng.lr is not None, "run python -m ml.train_match"
    pos = _pick_job(eng)
    req = eng.job_skills(pos)
    good = {"skills": set(req), "exp": 5, "edu": "Đại học", "location": eng.location[pos], "salary": None, "major": eng.category[pos]}
    bad = {"skills": {"Zzz"}, "exp": 0, "edu": "THPT", "location": "Nowhere", "salary": None, "major": "x"}
    jid = int(eng.job_ids[pos])
    assert eng.score_jobs(good, [jid], "lr-v1")[jid] > 0.75 > eng.score_jobs(bad, [jid], "lr-v1")[jid]
    assert abs(HEURISTIC_W.sum() - 1.0) < 1e-9


def test_level_fit_is_two_sided(eng):
    pos = next(i for i in range(len(eng.job_ids)) if eng.level[i] == "Mid")
    base = {"skills": set(), "edu": "Đại học", "location": eng.location[pos], "salary": None, "major": ""}
    f = lambda exp: eng.features([{**base, "exp": exp}], np.array([0]), np.array([pos]))[0][FEATURES.index("level_fit")]  # noqa: E731
    mid, junior, senior = f(3.0), f(0.5), f(8.0)
    assert mid == 1.0 and junior < mid and senior < mid  # under- and over-qualified both lose points
