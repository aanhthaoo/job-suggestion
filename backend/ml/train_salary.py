"""Salary model: RandomForest vs segment-median baseline. Run: python -m ml.train_salary

Split by hash(job_key) so the same posting never sits in both sets. Target: mid salary (million VND/month).
"""
import hashlib
import json
import sys
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from app.db import connect
from etl.common import EDU_RANK
from ml.matching import MODELS

CATS = ["category", "level", "location"]


def load_df() -> pd.DataFrame:
    conn = connect(retries=3)
    df = pd.read_sql("""SELECT j.job_key, j.category, j.level, j.location, j.exp_years_min AS exp, j.education,
                        (j.salary_min + j.salary_max) / 2.0 AS sal,
                        (SELECT COUNT(*) FROM job_skill js WHERE js.job_id=j.id) AS n_skills
                        FROM job_posting j WHERE j.salary_min > 0 AND j.salary_max > 0""", conn)
    conn.close()
    df["sal"] = df["sal"].astype(float)
    df["exp"] = df["exp"].astype(float)
    return df


def design(df: pd.DataFrame, columns=None) -> pd.DataFrame:
    X = pd.get_dummies(df[CATS], dtype=float)
    X["exp"] = df["exp"].astype(float)
    X["edu"] = df["education"].map(EDU_RANK).fillna(0)
    X["n_skills"] = df["n_skills"].astype(float)
    return X if columns is None else X.reindex(columns=columns, fill_value=0.0)


def is_test(key: str) -> bool:
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 5 == 0  # 20% test


def baseline_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    seg = train.groupby(["category", "level"])["sal"].median()
    cat = train.groupby("category")["sal"].median()
    glob = train["sal"].median()
    return np.array([seg.get((r.category, r.level), cat.get(r.category, glob)) for r in test.itertuples()])


def metrics(y, p) -> Dict[str, float]:
    return {"mae": round(float(np.mean(np.abs(y - p))), 3),
            "mape": round(float(np.mean(np.abs(y - p) / np.maximum(y, 1e-9))), 4)}


def main():
    df = load_df()
    mask = df.job_key.map(is_test)
    train, test = df[~mask].reset_index(drop=True), df[mask].reset_index(drop=True)
    Xtr = design(train)
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42, n_jobs=-1)
    rf.fit(Xtr, np.log1p(train.sal))
    p_rf = np.expm1(rf.predict(design(test, Xtr.columns)))
    p_base = baseline_predict(train, test)
    res = {"n_train": int(len(train)), "n_test": int(len(test)),
           "random_forest": metrics(test.sal.values, p_rf), "baseline_median": metrics(test.sal.values, p_base)}
    res["use_model"] = res["random_forest"]["mae"] < res["baseline_median"]["mae"]
    # final model on everything
    Xall = design(df)
    rf_all = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42, n_jobs=-1)
    rf_all.fit(Xall, np.log1p(df.sal))
    MODELS.mkdir(exist_ok=True)
    joblib.dump({"model": rf_all, "columns": list(Xall.columns), "use_model": res["use_model"]}, MODELS / "salary.joblib")
    (MODELS / "salary_metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


_CACHE: Optional[dict] = None


def predict_salary(category: str, level: str, location: str, exp: float, edu: str, n_skills: int) -> Optional[float]:
    global _CACHE
    if _CACHE is None:
        p = MODELS / "salary.joblib"
        if not p.exists():
            return None
        _CACHE = joblib.load(p)
    row = pd.DataFrame([{"category": category, "level": level, "location": location, "exp": exp,
                         "education": edu, "n_skills": n_skills}])
    X = design(row, _CACHE["columns"])
    return round(float(np.expm1(_CACHE["model"].predict(X)[0])), 1)


if __name__ == "__main__":
    sys.exit(main())
