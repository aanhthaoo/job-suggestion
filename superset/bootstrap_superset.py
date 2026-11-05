"""Bootstrap Superset: register Postgres DB, create datasets, charts (with a
working query_context so they render data), and a dashboard that contains them.

Idempotent by name — safe to re-run; existing charts/dashboard are updated.
Talks to the Superset REST API (tested against Superset 6.1).

Env:
  SUPERSET_URL   (default http://localhost:8088)
  SUPERSET_USER  (default admin)
  SUPERSET_PASS  (default admin)
  DB_URI         sqlalchemy URI for the analytics DB
  DB_NAME_LABEL  display name of the DB connection in Superset
"""
import os
import json
import uuid
import sqlite3
import requests

SUPERSET_URL = os.getenv("SUPERSET_URL", "http://localhost:8088").rstrip("/")
SUPERSET_USER = os.getenv("SUPERSET_USER", "admin")
SUPERSET_PASS = os.getenv("SUPERSET_PASS", "admin")
DB_URI = os.getenv(
    "DB_URI",
    "postgresql+psycopg2://postgres:postgres@postgres:5432/jobportal",
)
DB_NAME = os.getenv("DB_NAME_LABEL", "JobPortal Postgres")
SCHEMA = "public"
# Superset metadata DB (sqlite). The REST API in Superset 6.x does not expose the
# dashboard<->chart link, so we populate dashboard_slices directly when the file
# is reachable (superset-init mounts the superset_home volume).
SUPERSET_DB_PATH = os.getenv("SUPERSET_DB_PATH", "/app/superset_home/superset.db")

DATASETS = ["job_posting", "application", "v_skill_supply_demand", "v_skill_trend_quarter",
            "v_skill_salary_premium", "v_funnel_long", "v_match_score_hist", "v_match_vs_outcome"]
STALE_CHART_NAMES = ["(2) Xu hướng lương p25/p50/p75 theo tháng, triệu VND (ngày đăng (mô phỏng))",
                     "Lương trung vị theo ngành (triệu VND)", "Lương trung vị theo cấp bậc (triệu VND)"]
LEGACY_TABLES = ["jobs", "job_skills", "applications", "users", "companies"]

session = requests.Session()


def _login():
    r = session.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={"username": SUPERSET_USER, "password": SUPERSET_PASS,
              "provider": "db", "refresh": True},
        timeout=30,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    c = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", timeout=30)
    c.raise_for_status()
    session.headers["X-CSRFToken"] = c.json()["result"]
    session.headers["Referer"] = SUPERSET_URL


def _list(path, match_field, match_value):
    r = session.get(f"{SUPERSET_URL}{path}?q=(page_size:500)", timeout=30)
    r.raise_for_status()
    for item in r.json().get("result", []):
        if item.get(match_field) == match_value:
            return item
    return None


def ensure_database():
    existing = _list("/api/v1/database/", "database_name", DB_NAME)
    if existing:
        return existing["id"]
    r = session.post(
        f"{SUPERSET_URL}/api/v1/database/",
        json={"database_name": DB_NAME, "sqlalchemy_uri": DB_URI, "expose_in_sqllab": True},
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"create database failed {r.status_code}: {r.text[:400]}")
    body = r.json()
    return body.get("id") or body.get("result", {}).get("id")


def ensure_dataset(db_id, table):
    existing = _list("/api/v1/dataset/", "table_name", table)
    if existing and existing.get("schema") == SCHEMA:
        return existing["id"]
    r = session.post(
        f"{SUPERSET_URL}/api/v1/dataset/",
        json={"database": db_id, "schema": SCHEMA, "table_name": table},
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"create dataset {table} failed {r.status_code}: {r.text[:400]}")
    body = r.json()
    return body.get("id") or body.get("result", {}).get("id")


def adhoc_sql_metric(expr, label, option_name):
    return {
        "expressionType": "SQL",
        "aggregate": None,
        "column": None,
        "columnType": None,
        "sqlExpression": expr,
        "label": label,
        "hasCustomLabel": True,
        "optionName": option_name,
    }


def count_metric(col="id", label=None, option_name=None):
    return adhoc_metric(col, "COUNT", label, option_name)


def adhoc_metric(col, agg, label=None, option_name=None):
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": col, "type": "TEXT", "is_dttm": False},
        "aggregate": agg,
        "columnType": "TEXT",
        "label": label or f"{agg}({col})",
        "hasCustomLabel": bool(label),
        "optionName": option_name or f"metric_{agg.lower()}_{col}",
        "sqlExpression": None,
    }


def build_query_context(ds_id, columns, metrics, row_limit, form_data, time_grain=None,
                        granularity=None, time_range=None, where=None):
    query = {
        "columns": columns,
        "metrics": metrics,
        "row_limit": row_limit,
        "order_desc": True,
        "filters": [],
        "orderby": [],
        "annotation_layers": [],
        "series_columns": [],
        "series_limit": 0,
        "time_offsets": [],
        "extras": {"time_grain_sqla": time_grain} if time_grain else {},
        "applied_time_extras": {},
    }
    if where:
        query["extras"]["where"] = where
    if granularity:
        # Superset only truncates + groups by time when the synthetic "__timestamp"
        # dimension is requested (QueryObject._set_is_timeseries checks DTTM_ALIAS);
        # granularity names the real datetime column and time_grain_sqla the bucket.
        query["columns"] = ["__timestamp", *columns]
        query["granularity"] = granularity
        query["time_range"] = time_range or "No filter"
        query["is_timeseries"] = True
        query["extras"].setdefault("time_grain_sqla", time_grain or "P1D")
    return {
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [query],
        "form_data": form_data,
        "result_format": "json",
        "result_type": "full",
    }


# --------------------------------------------------------------------------- chart specs
SIM = "(mô phỏng)"


def sum_metric(col, label):
    return adhoc_metric(col, "SUM", label, f"metric_sum_{col}")


def max_metric(col, label):
    return adhoc_metric(col, "MAX", label, f"metric_max_{col}")


def sql_filter(expr):
    return {"expressionType": "SQL", "clause": "WHERE", "sqlExpression": expr,
            "comparator": None, "operator": None, "subject": None}


def chart_specs(ds):
    """Two dashboards. Returns list of specs with a `dash` key ('A' market, 'B' recruiting)."""
    def src(t):
        return f"{ds[t]}__table"

    def bar(dash, name, table, x, metrics, limit, horizontal=False, groupby=None, where=None):
        groupby = groupby or []
        fd = {"datasource": src(table), "viz_type": "echarts_timeseries_bar", "x_axis": x, "groupby": groupby,
              "metrics": metrics, "adhoc_filters": [sql_filter(where)] if where else [], "order_desc": True,
              "row_limit": limit, "orientation": "horizontal" if horizontal else "vertical", "show_value": True,
              "show_legend": bool(groupby), "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"}
        return dict(dash=dash, name=name, table=table, viz="echarts_timeseries_bar", columns=[x, *groupby],
                    metrics=metrics, row_limit=limit, where=where, form_data=fd)

    def line(dash, name, table, tcol, metrics, grain, where=None, groupby=None):
        groupby = groupby or []
        fd = {"datasource": src(table), "viz_type": "echarts_timeseries_line", "x_axis": tcol,
              "granularity_sqla": tcol, "time_grain_sqla": grain, "time_range": "No filter", "groupby": groupby,
              "metrics": metrics, "adhoc_filters": [sql_filter(where)] if where else [], "order_desc": True,
              "row_limit": 500, "show_legend": True, "rich_tooltip": True, "y_axis_format": "SMART_NUMBER",
              "markerEnabled": True, "x_axis_time_format": "%Y-%m-%d"}
        return dict(dash=dash, name=name, table=table, viz="echarts_timeseries_line", columns=groupby,
                    metrics=metrics, row_limit=500, granularity=tcol, time_grain=grain, where=where, form_data=fd)

    def big(dash, name, table, metric, fmt="SMART_NUMBER"):
        fd = {"datasource": src(table), "viz_type": "big_number_total", "metric": metric, "adhoc_filters": [],
              "subheader": "", "y_axis_format": fmt}
        return dict(dash=dash, name=name, table=table, viz="big_number_total", columns=[], metrics=[metric],
                    row_limit=1, form_data=fd)

    mid = "(salary_min + salary_max) / 2"
    pct = lambda q, lab: adhoc_sql_metric(  # noqa: E731
        f"percentile_cont({q}) WITHIN GROUP (ORDER BY {mid})", lab, f"metric_pct_{lab}")
    sal_where = "salary_min > 0"
    return [
        # ---- Dashboard A: thị trường lao động
        bar("A", f"(1) Cung - cầu kỹ năng: số ứng viên vs số tin, top 15 {SIM}", "v_skill_supply_demand", "skill",
            [sum_metric("n_candidates", "Số ứng viên"), sum_metric("n_jobs", "Số tin cần kỹ năng")], 15),
        bar("A", "(2) Lương p25/p50/p75 theo cấp bậc, triệu VND (dữ liệu lương thật)", "job_posting", "level",
            [pct(0.25, "p25"), pct(0.5, "p50"), pct(0.75, "p75")], 10, where=sal_where),
        bar("A", "(2b) Lương p25/p50/p75 theo ngành, triệu VND (dữ liệu lương thật)", "job_posting", "category",
            [pct(0.25, "p25"), pct(0.5, "p50"), pct(0.75, "p75")], 20, True, where=sal_where),
        line("A", f"(2c) Minh họa xu hướng lương theo tháng, triệu VND (ngày đăng {SIM} - KHÔNG phản ánh thị trường)",
             "job_posting", "posted_at", [pct(0.25, "p25"), pct(0.5, "p50"), pct(0.75, "p75")], "P1M", sal_where),
        bar("A", f"Chỉ số khan hiếm kỹ năng (số tin / số ứng viên) {SIM}", "v_skill_supply_demand", "skill",
            [max_metric("scarcity_index", "Khan hiếm")], 15, True, where="n_jobs >= 20"),
        bar("A", f"Kỹ năng tăng nhanh nhất giữa 2 quý gần nhất (ngày đăng {SIM})", "v_skill_trend_quarter",
            "skill", [sum_metric("change", "Chênh lệch số tin")], 15, True),
        bar("A", "Số tin theo ngành", "job_posting", "category", [count_metric("id", "Số tin")], 20, True),
        bar("A", "Số tin theo địa điểm", "job_posting", "location", [count_metric("id", "Số tin")], 10),
        bar("A", "Chênh lệch lương theo kỹ năng so với trung vị ngành (triệu VND)", "v_skill_salary_premium",
            "skill", [max_metric("premium_vs_category_median", "Chênh lệch")], 15, True),
        big("A", "Tỷ lệ tin công khai mức lương (%)", "job_posting",
            adhoc_sql_metric("100.0 * COUNT(salary_min) / NULLIF(COUNT(*), 0)", "% công khai lương", "metric_disclosed"),
            ".1f"),
        # ---- Dashboard B: tuyển dụng
        bar("B", f"(3) Tỷ lệ chuyển đổi: nộp đơn → sàng lọc → phỏng vấn → offer, theo nguồn {SIM}",
            "v_funnel_long", "stage", [sum_metric("n", "Số đơn")], 10, groupby=["source"],
            where="is_simulated"),
        bar("B", f"Phân bố Matching Score của các đơn {SIM}", "v_match_score_hist", "score_bin",
            [sum_metric("n", "Số đơn")], 12),
        bar("B", f"Tỷ lệ qua phỏng vấn theo khoảng điểm khớp (kiểm tra hiệu chuẩn) {SIM}", "v_match_vs_outcome",
            "score_band", [max_metric("interview_rate", "Tỷ lệ phỏng vấn"), max_metric("offer_rate", "Tỷ lệ offer")], 5),
        big("B", f"Thời gian phản hồi trung bình (ngày) {SIM}", "application",
            adhoc_sql_metric("AVG(EXTRACT(EPOCH FROM (updated_at - applied_at)) / 86400)", "Ngày", "metric_resp_days"),
            ".1f"),
        line("B", f"Số đơn ứng tuyển theo tuần {SIM}", "application", "applied_at", [count_metric("id", "Số đơn")], "P1W"),
    ]


def ensure_charts(ds):
    ids = {"A": {}, "B": {}}
    for spec in chart_specs(ds):
        ds_id = ds[spec["table"]]
        qc = build_query_context(ds_id, spec["columns"], spec["metrics"], spec["row_limit"], spec["form_data"],
                                 spec.get("time_grain"), spec.get("granularity"), where=spec.get("where"))
        payload = {"datasource_id": ds_id, "datasource_type": "table", "slice_name": spec["name"],
                   "viz_type": spec["viz"], "params": json.dumps(spec["form_data"]), "query_context": json.dumps(qc)}
        existing = _list("/api/v1/chart/", "slice_name", spec["name"])
        if existing:
            r = session.put(f"{SUPERSET_URL}/api/v1/chart/{existing['id']}", json=payload, timeout=60)
            cid = existing["id"]
        else:
            r = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=payload, timeout=60)
            body = r.json()
            cid = body.get("id") or body.get("result", {}).get("id")
        if r.status_code not in (200, 201):
            raise RuntimeError(f"save chart '{spec['name']}' failed {r.status_code}: {r.text[:400]}")
        ids[spec["dash"]][spec["name"]] = cid
        spec["_qc"] = qc
    return ids, chart_specs_cache(ds)


def chart_specs_cache(ds):
    return {s["name"]: s for s in chart_specs(ds)}


def verify_charts(ds, ids):
    """Run every chart's query; each must return >= 1 row. Prints a confirmation table. Returns #failures."""
    specs = chart_specs_cache(ds)
    bad = 0
    print(f"{'chart':95s} rows")
    for dash, charts in ids.items():
        for name in charts:
            s = specs[name]
            qc = build_query_context(ds[s["table"]], s["columns"], s["metrics"], s["row_limit"], s["form_data"],
                                     s.get("time_grain"), s.get("granularity"), where=s.get("where"))
            r = session.post(f"{SUPERSET_URL}/api/v1/chart/data", json=qc, timeout=120)
            rows = -1
            if r.status_code == 200:
                res = r.json()["result"][0]
                rows = len(res.get("data", []))
            flag = "OK" if rows >= 1 else "FAIL"
            bad += rows < 1
            print(f"[{dash}] {name[:90]:90s} {rows:4d} {flag}")
    return bad


def build_position_json(chart_ids):
    pos = {"DASHBOARD_VERSION_KEY": "v2", "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {}}}
    grid_children, items = [], list(chart_ids.items())
    for ri, i in enumerate(range(0, len(items), 2)):
        row_id = f"ROW-{ri}-{uuid.uuid4().hex[:8]}"
        cells = []
        for name, cid in items[i:i + 2]:
            key = f"CHART-{uuid.uuid4().hex[:8]}"
            pos[key] = {"id": key, "type": "CHART", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id],
                        "meta": {"chartId": cid, "sliceName": name, "width": 6, "height": 50}}
            cells.append(key)
        pos[row_id] = {"id": row_id, "type": "ROW", "children": cells, "parents": ["ROOT_ID", "GRID_ID"],
                       "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        grid_children.append(row_id)
    pos["GRID_ID"] = {"id": "GRID_ID", "type": "GRID", "children": grid_children, "parents": ["ROOT_ID"]}
    pos["ROOT_ID"] = {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]}
    return pos


def ensure_dashboard(title, slug, chart_ids):
    payload = {"dashboard_title": title, "slug": slug, "published": True,
               "position_json": json.dumps(build_position_json(chart_ids))}
    r = session.get(f"{SUPERSET_URL}/api/v1/dashboard/?q=(page_size:200)", timeout=30)
    r.raise_for_status()
    existing = next((i for i in r.json().get("result", []) if i.get("slug") == slug), None)
    if existing:
        r = session.put(f"{SUPERSET_URL}/api/v1/dashboard/{existing['id']}", json=payload, timeout=60)
        did = existing["id"]
    else:
        r = session.post(f"{SUPERSET_URL}/api/v1/dashboard/", json=payload, timeout=60)
        body = r.json()
        did = body.get("id") or body.get("result", {}).get("id")
    if r.status_code not in (200, 201):
        raise RuntimeError(f"save dashboard failed {r.status_code}: {r.text[:400]}")
    return did


def link_dashboard_charts(dash_id, chart_ids):
    """Populate dashboard_slices directly (not exposed by the Superset 6.x API). Idempotent."""
    if not os.path.exists(SUPERSET_DB_PATH):
        print(f"[superset] WARN metadata DB not found at {SUPERSET_DB_PATH}; skipping dashboard<->chart link")
        return False
    conn = sqlite3.connect(SUPERSET_DB_PATH, timeout=30)
    try:
        cur = conn.cursor()
        for cid in chart_ids.values():
            cur.execute("INSERT OR IGNORE INTO dashboard_slices (dashboard_id, slice_id) VALUES (?, ?)", (dash_id, cid))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM dashboard_slices WHERE dashboard_id=?", (dash_id,))
        print(f"[superset] dashboard {dash_id}: {cur.fetchone()[0]} charts linked")
        return True
    finally:
        conn.close()


def _unlink_chart(cid):
    if os.path.exists(SUPERSET_DB_PATH):
        conn = sqlite3.connect(SUPERSET_DB_PATH, timeout=30)
        try:
            conn.execute("DELETE FROM dashboard_slices WHERE slice_id=?", (cid,))
            conn.commit()
        finally:
            conn.close()


def cleanup_legacy():
    """Remove the pre-v2 dashboard/charts/datasets (they point at tables that no longer exist)."""
    r = session.get(f"{SUPERSET_URL}/api/v1/chart/?q=(page_size:500)", timeout=30)
    r.raise_for_status()
    for item in r.json().get("result", []):
        ds_name = str(item.get("datasource_name_text") or "")
        if ds_name.split(".")[-1] in LEGACY_TABLES:
            _unlink_chart(item["id"])
            session.delete(f"{SUPERSET_URL}/api/v1/chart/{item['id']}", timeout=60)
            print(f"[superset] removed legacy chart {item['id']} ({item.get('slice_name')})")
    for item in r.json().get("result", []):
        if item.get("slice_name") in STALE_CHART_NAMES:
            _unlink_chart(item["id"])
            session.delete(f"{SUPERSET_URL}/api/v1/chart/{item['id']}", timeout=60)
            print(f"[superset] removed superseded chart {item['id']} ({item['slice_name']})")
    d = _list("/api/v1/dashboard/", "slug", "job-portal-bi")
    if d:
        session.delete(f"{SUPERSET_URL}/api/v1/dashboard/{d['id']}", timeout=60)
        print("[superset] removed legacy dashboard job-portal-bi")
    for t in LEGACY_TABLES:
        existing = _list("/api/v1/dataset/", "table_name", t)
        if existing:
            session.delete(f"{SUPERSET_URL}/api/v1/dataset/{existing['id']}", timeout=60)


def main():
    _login()
    db_id = ensure_database()
    print(f"[superset] database id={db_id}")
    cleanup_legacy()
    ds = {t: ensure_dataset(db_id, t) for t in DATASETS}
    print(f"[superset] datasets: {ds}")
    ids, _ = ensure_charts(ds)
    for slug, key, title in (("thi-truong-lao-dong", "A", "A. Thị trường lao động"),
                             ("tuyen-dung", "B", "B. Hiệu quả tuyển dụng")):
        did = ensure_dashboard(title, slug, ids[key])
        link_dashboard_charts(did, ids[key])
        print(f"[superset] open {SUPERSET_URL}/superset/dashboard/{slug}/")
    bad = verify_charts(ds, ids)
    print(f"[superset] verification: {sum(len(v) for v in ids.values()) - bad} OK, {bad} FAIL")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
