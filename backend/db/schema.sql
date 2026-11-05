-- Job suggestion system schema (idempotent). Applied by app/seed_db.py.
-- Salary unit: million VND / month.

CREATE TABLE IF NOT EXISTS company (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    location  TEXT,
    industry  TEXT,
    size      TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('candidate','employer','admin')),
    company_id    INT REFERENCES company(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_posting (
    id            SERIAL PRIMARY KEY,
    job_key       TEXT NOT NULL UNIQUE,
    company_id    INT REFERENCES company(id),
    title         TEXT NOT NULL,
    category      TEXT,
    location      TEXT,
    level         TEXT,
    exp_years_min NUMERIC(4,1) DEFAULT 0,
    education     TEXT,
    salary_min    NUMERIC(8,2),
    salary_max    NUMERIC(8,2),
    description   TEXT,
    requirements  TEXT,
    benefits      TEXT,
    contract_type TEXT,
    working_hours TEXT,
    soft_skills   TEXT[],
    languages_required TEXT,
    source        TEXT NOT NULL CHECK (source IN ('vietjobs','synthetic','fixture')),
    status        TEXT NOT NULL DEFAULT 'active',
    posted_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_job_category ON job_posting(category);
CREATE INDEX IF NOT EXISTS idx_job_location ON job_posting(location);
CREATE INDEX IF NOT EXISTS idx_job_company  ON job_posting(company_id);

CREATE TABLE IF NOT EXISTS skill (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    aliases TEXT,
    type    TEXT NOT NULL DEFAULT 'tech' CHECK (type IN ('tech','soft'))
);

CREATE TABLE IF NOT EXISTS job_skill (
    job_id   INT NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skill(id),
    weight   NUMERIC(3,1) NOT NULL DEFAULT 1.0,
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS candidate (
    id              SERIAL PRIMARY KEY,
    user_id         INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name       TEXT NOT NULL,
    major           TEXT,
    gpa             NUMERIC(3,2),
    exp_years       NUMERIC(4,1) DEFAULT 0,
    education       TEXT,
    location        TEXT,
    expected_salary NUMERIC(8,2),
    is_simulated    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS candidate_skill (
    candidate_id INT NOT NULL REFERENCES candidate(id) ON DELETE CASCADE,
    skill_id     INT NOT NULL REFERENCES skill(id),
    source       TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('cv','manual')),
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE IF NOT EXISTS cv_document (
    id                 SERIAL PRIMARY KEY,
    candidate_id       INT NOT NULL REFERENCES candidate(id) ON DELETE CASCADE,
    filename           TEXT,
    raw_text           TEXT,
    parsed_json        JSONB,
    health_score       NUMERIC(5,2),
    health_issues_json JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- stage_reached: 0 applied, 1 screening, 2 interview, 3 offer (funnel depth)
CREATE TABLE IF NOT EXISTS application (
    id            SERIAL PRIMARY KEY,
    candidate_id  INT NOT NULL REFERENCES candidate(id) ON DELETE CASCADE,
    job_id        INT NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'applied'
                  CHECK (status IN ('applied','screening','interview','offer','rejected')),
    stage_reached SMALLINT NOT NULL DEFAULT 0,
    match_score   NUMERIC(5,4),
    source        TEXT NOT NULL DEFAULT 'search' CHECK (source IN ('recommend','search')),
    applied_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_simulated  BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (candidate_id, job_id)
);

CREATE TABLE IF NOT EXISTS matching_result (
    candidate_id   INT NOT NULL REFERENCES candidate(id) ON DELETE CASCADE,
    job_id         INT NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    score          NUMERIC(5,4) NOT NULL,
    components_json JSONB,
    matched_skills TEXT[],
    missing_skills TEXT[],
    model_version  TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (candidate_id, job_id, model_version)
);

CREATE TABLE IF NOT EXISTS cv_suggestion (
    cv_id        INT NOT NULL REFERENCES cv_document(id) ON DELETE CASCADE,
    job_id       INT NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    content_json JSONB NOT NULL,
    source       TEXT NOT NULL CHECK (source IN ('gemini','fallback')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (cv_id, job_id)
);

ALTER TABLE job_posting DROP CONSTRAINT IF EXISTS job_posting_source_check;
ALTER TABLE job_posting ADD CONSTRAINT job_posting_source_check
    CHECK (source IN ('vietjobs','synthetic','fixture','employer'));
ALTER TABLE job_posting ADD COLUMN IF NOT EXISTS benefits TEXT;
ALTER TABLE job_posting ADD COLUMN IF NOT EXISTS contract_type TEXT;
ALTER TABLE job_posting ADD COLUMN IF NOT EXISTS working_hours TEXT;
ALTER TABLE job_posting ADD COLUMN IF NOT EXISTS soft_skills TEXT[];
ALTER TABLE job_posting ADD COLUMN IF NOT EXISTS languages_required TEXT;

-- ---------------------------------------------------------------- BI views
CREATE OR REPLACE VIEW v_skill_supply_demand AS
SELECT s.name AS skill,
       COALESCE(c.n, 0) AS n_candidates,
       COALESCE(j.n, 0) AS n_jobs,
       ROUND(COALESCE(j.n, 0)::numeric / NULLIF(COALESCE(c.n, 0), 0), 3) AS scarcity_index
FROM skill s
LEFT JOIN (SELECT skill_id, COUNT(*) n FROM candidate_skill GROUP BY skill_id) c ON c.skill_id = s.id
LEFT JOIN (SELECT skill_id, COUNT(*) n FROM job_skill GROUP BY skill_id) j ON j.skill_id = s.id;

CREATE OR REPLACE VIEW v_salary_by_segment AS
SELECT category, level, location,
       to_char(date_trunc('month', posted_at), 'YYYY-MM') AS month,
       COUNT(*) AS n_jobs,
       percentile_cont(0.25) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2) AS p25,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2) AS p50,
       percentile_cont(0.75) WITHIN GROUP (ORDER BY (salary_min + salary_max) / 2) AS p75
FROM job_posting
WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL AND salary_min > 0
GROUP BY category, level, location, date_trunc('month', posted_at);

CREATE OR REPLACE VIEW v_funnel AS
SELECT a.source,
       COUNT(*)                                         AS applied,
       COUNT(*) FILTER (WHERE a.stage_reached >= 1)     AS screening,
       COUNT(*) FILTER (WHERE a.stage_reached >= 2)     AS interview,
       COUNT(*) FILTER (WHERE a.stage_reached >= 3)     AS offer,
       a.is_simulated
FROM application a
GROUP BY a.source, a.is_simulated;

CREATE OR REPLACE VIEW v_match_vs_outcome AS
SELECT CASE WHEN match_score >= 0.75 THEN '>=0.75'
            WHEN match_score >= 0.55 THEN '0.55-0.75'
            ELSE '<0.55' END AS score_band,
       COUNT(*) AS n_applications,
       ROUND(AVG((stage_reached >= 2)::int)::numeric, 3) AS interview_rate,
       ROUND(AVG((stage_reached >= 3)::int)::numeric, 3) AS offer_rate
FROM application
WHERE match_score IS NOT NULL
GROUP BY 1;

CREATE OR REPLACE VIEW v_skill_trend_quarter AS
SELECT s.name AS skill,
       COUNT(*) FILTER (WHERE j.posted_at >= now() - interval '90 days') AS n_last,
       COUNT(*) FILTER (WHERE j.posted_at < now() - interval '90 days'
                          AND j.posted_at >= now() - interval '180 days') AS n_prev,
       COUNT(*) FILTER (WHERE j.posted_at >= now() - interval '90 days')
         - COUNT(*) FILTER (WHERE j.posted_at < now() - interval '90 days'
                              AND j.posted_at >= now() - interval '180 days') AS change
FROM skill s JOIN job_skill js ON js.skill_id = s.id JOIN job_posting j ON j.id = js.job_id
GROUP BY s.name;

CREATE OR REPLACE VIEW v_skill_salary_premium AS
WITH j AS (SELECT id, category, (salary_min + salary_max) / 2 AS mid FROM job_posting WHERE salary_min > 0),
     med AS (SELECT category, percentile_cont(0.5) WITHIN GROUP (ORDER BY mid) AS m FROM j GROUP BY category)
SELECT s.name AS skill, COUNT(*) AS n_jobs,
       ROUND(AVG(j.mid - med.m)::numeric, 2) AS premium_vs_category_median
FROM j JOIN med USING (category) JOIN job_skill js ON js.job_id = j.id JOIN skill s ON s.id = js.skill_id
GROUP BY s.name HAVING COUNT(*) >= 15;

CREATE OR REPLACE VIEW v_funnel_long AS
SELECT source, is_simulated, '1. Nop don' AS stage, applied AS n FROM v_funnel
UNION ALL SELECT source, is_simulated, '2. Sang loc', screening FROM v_funnel
UNION ALL SELECT source, is_simulated, '3. Phong van', interview FROM v_funnel
UNION ALL SELECT source, is_simulated, '4. Offer', offer FROM v_funnel;

CREATE OR REPLACE VIEW v_match_score_hist AS
SELECT (LEAST(FLOOR(match_score * 10), 9) / 10.0)::numeric(2,1)::text AS score_bin, COUNT(*) AS n
FROM application WHERE match_score IS NOT NULL GROUP BY 1;
