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

DATASETS = ["jobs", "job_skills", "applications", "users", "companies"]

# Charts from earlier iterations of this script, superseded by better specs. They
# are deleted so the dashboard never keeps empty tiles for them.
STALE_CHART_NAMES = ["Việc làm đăng mới theo tháng", "Mức lương trung bình theo tháng"]

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
                        granularity=None, time_range=None):
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


def chart_specs(ds):
    """Return list of chart definitions. ds: table -> dataset id."""
    def src(t):
        return f"{ds[t]}__table"

    specs = []

    # Big numbers (plugin key in Superset 6.x is big_number_total)
    specs.append(dict(
        name="Tổng số việc làm", table="jobs", viz="big_number_total", columns=[],
        metrics=[count_metric("id", "Tổng việc làm")], row_limit=1,
        form_data={"datasource": src("jobs"), "viz_type": "big_number_total",
                   "metric": count_metric("id", "Tổng việc làm"),
                   "adhoc_filters": [], "subheader": "", "y_axis_format": "SMART_NUMBER"},
    ))
    specs.append(dict(
        name="Tổng hồ sơ ứng tuyển", table="applications", viz="big_number_total", columns=[],
        metrics=[count_metric("id", "Tổng ứng tuyển")], row_limit=1,
        form_data={"datasource": src("applications"), "viz_type": "big_number_total",
                   "metric": count_metric("id", "Tổng ứng tuyển"),
                   "adhoc_filters": [], "subheader": "", "y_axis_format": "SMART_NUMBER"},
    ))
    # Categorical bars
    specs.append(dict(
        name="Việc làm theo địa điểm", table="jobs", viz="echarts_timeseries_bar",
        columns=["location"], metrics=[count_metric("id")], row_limit=100,
        form_data={"datasource": src("jobs"), "viz_type": "echarts_timeseries_bar",
                   "x_axis": "location", "groupby": [], "metrics": [count_metric("id")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 100,
                   "orientation": "vertical", "show_value": True, "show_legend": False,
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"},
    ))
    specs.append(dict(
        name="Ứng tuyển theo trạng thái", table="applications", viz="echarts_timeseries_bar",
        columns=["status"], metrics=[count_metric("id")], row_limit=100,
        form_data={"datasource": src("applications"), "viz_type": "echarts_timeseries_bar",
                   "x_axis": "status", "groupby": [], "metrics": [count_metric("id")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 100,
                   "orientation": "vertical", "show_value": True, "show_legend": False,
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"},
    ))
    specs.append(dict(
        name="Kỹ năng được yêu cầu nhiều nhất", table="job_skills",
        viz="echarts_timeseries_bar", columns=["skill"], metrics=[count_metric("skill")],
        row_limit=15,
        form_data={"datasource": src("job_skills"), "viz_type": "echarts_timeseries_bar",
                   "x_axis": "skill", "groupby": [], "metrics": [count_metric("skill")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 15,
                   "orientation": "horizontal", "show_value": True, "show_legend": False,
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"},
    ))
    # Pies. Superset 6.x reads formData.metric (singular) when rendering the pie,
    # so form_data must carry metric + sort_by_metric, not only the metrics array.
    def pie(name, col, donut, label):
        m = count_metric("id", label, f"metric_{col}")
        return dict(
            name=name, table="jobs", viz="pie",
            columns=[col], metrics=[m], row_limit=100,
            form_data={"datasource": src("jobs"), "viz_type": "pie",
                       "groupby": [col], "metric": m, "metrics": [m],
                       "sort_by_metric": m, "adhoc_filters": [],
                       "row_limit": 100, "donut": donut,
                       "inner_radius": 35 if donut else 0, "outer_radius": 70,
                       "show_labels": True, "label_type": "key_value",
                       "tooltip_label_type": "key_value",
                       "number_format": "SMART_NUMBER", "date_format": "smart_date",
                       "show_legend": True, "legend_type": "scroll",
                       "legend_orientation": "top", "color_scheme": "supersetColors",
                       "time_range": "No filter"},
        )

    specs.append(pie("Việc làm theo loại (job_type)", "job_type", False, "Số việc làm"))
    specs.append(pie("Việc làm theo hình thức (work_mode)", "work_mode", True, "Số việc làm"))
    # Trend charts (time grain + granularity so Superset aggregates the series)
    specs.append(dict(
        name="Ứng tuyển theo thời gian", table="applications",
        viz="echarts_timeseries_line", columns=[], metrics=[count_metric("id", "Số ứng tuyển")],
        row_limit=300, granularity="applied_at", time_grain="P1W",
        form_data={"datasource": src("applications"), "viz_type": "echarts_timeseries_line",
                   "x_axis": "applied_at", "granularity_sqla": "applied_at",
                   "time_grain_sqla": "P1W", "time_range": "No filter", "groupby": [],
                   "metrics": [count_metric("id", "Số ứng tuyển")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 300,
                   "show_legend": False, "rich_tooltip": True, "only_total": True,
                   "y_axis_format": "SMART_NUMBER", "markerEnabled": True,
                   "markLine": "undefined", "x_axis_time_format": "%m/%d/%Y %H:%M:%S"},
    ))
    specs.append(dict(
        name="Xu hướng ứng tuyển theo trạng thái (tuần)", table="applications",
        viz="echarts_timeseries_line", columns=["status"],
        metrics=[count_metric("id", "Số ứng tuyển")], row_limit=300,
        granularity="applied_at", time_grain="P1W",
        form_data={"datasource": src("applications"), "viz_type": "echarts_timeseries_line",
                   "x_axis": "applied_at", "granularity_sqla": "applied_at",
                   "time_grain_sqla": "P1W", "time_range": "No filter",
                   "groupby": ["status"],
                   "metrics": [count_metric("id", "Số ứng tuyển")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 300,
                   "show_legend": True, "legendType": "scroll", "legendOrientation": "top",
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER",
                   "markerEnabled": True, "x_axis_time_format": "%m/%d/%Y %H:%M:%S"},
    ))
    specs.append(dict(
        name="Việc làm đăng theo tuần", table="jobs",
        viz="echarts_timeseries_bar", columns=[], metrics=[count_metric("id", "Số việc làm")],
        row_limit=300, granularity="posted_at", time_grain="P1W",
        form_data={"datasource": src("jobs"), "viz_type": "echarts_timeseries_bar",
                   "x_axis": "posted_at", "granularity_sqla": "posted_at",
                   "time_grain_sqla": "P1W", "time_range": "No filter", "groupby": [],
                   "metrics": [count_metric("id", "Số việc làm")],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 300,
                   "orientation": "vertical", "show_value": True, "show_legend": False,
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"},
    ))
    acceptance = adhoc_sql_metric(
        "100.0 * SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)",
        "Tỷ lệ trúng tuyển (%)", "metric_acceptance_rate",
    )
    specs.append(dict(
        name="Tỷ lệ trúng tuyển theo tuần", table="applications",
        viz="echarts_timeseries_line", columns=[], metrics=[acceptance], row_limit=300,
        granularity="applied_at", time_grain="P1W",
        form_data={"datasource": src("applications"), "viz_type": "echarts_timeseries_line",
                   "x_axis": "applied_at", "granularity_sqla": "applied_at",
                   "time_grain_sqla": "P1W", "time_range": "No filter", "groupby": [],
                   "metrics": [acceptance], "adhoc_filters": [], "order_desc": True,
                   "row_limit": 300, "show_legend": False, "rich_tooltip": True,
                   "only_total": True, "y_axis_format": ".2f", "markerEnabled": True,
                   "x_axis_time_format": "%m/%d/%Y %H:%M:%S"},
    ))
    avg_salary = adhoc_metric("salary_min", "AVG", "Lương trung bình (VND)")
    specs.append(dict(
        name="Mức lương trung bình theo địa điểm", table="jobs",
        viz="echarts_timeseries_bar", columns=["location"], metrics=[avg_salary], row_limit=100,
        form_data={"datasource": src("jobs"), "viz_type": "echarts_timeseries_bar",
                   "x_axis": "location", "groupby": [], "metrics": [avg_salary],
                   "adhoc_filters": [], "order_desc": True, "row_limit": 100,
                   "orientation": "horizontal", "show_value": True, "show_legend": False,
                   "rich_tooltip": True, "y_axis_format": "SMART_NUMBER"},
    ))
    # Table (requires table_timestamp: a datetime column in the dataset)
    specs.append(dict(
        name="Bảng việc làm (chi tiết)", table="jobs", viz="table",
        columns=["title", "company_name", "location", "job_type", "work_mode",
                 "salary_min", "salary_max"],
        metrics=[], row_limit=50,
        form_data={"datasource": src("jobs"), "viz_type": "table", "query_mode": "raw",
                   "table_timestamp": "posted_at", "metrics": [],
                   "all_columns": ["title", "company_name", "location", "job_type",
                                   "work_mode", "salary_min", "salary_max"],
                   "percent_metrics": [], "adhoc_filters": [], "row_limit": 50,
                   "order_by_cols": [], "show_cell_bars": True,
                   "table_timestamp_format": "smart_date", "order_desc": True},
    ))
    return specs


def ensure_charts(ds):
    ids = {}
    for spec in chart_specs(ds):
        ds_id = ds[spec["table"]]
        form_data = spec["form_data"]
        qc = build_query_context(
            ds_id, spec["columns"], spec["metrics"], spec["row_limit"],
            form_data, spec.get("time_grain"), spec.get("granularity"),
        )
        payload = {
            "datasource_id": ds_id,
            "datasource_type": "table",
            "slice_name": spec["name"],
            "viz_type": spec["viz"],
            "params": json.dumps(form_data),
            "query_context": json.dumps(qc),
        }
        existing = _list("/api/v1/chart/", "slice_name", spec["name"])
        if existing:
            r = session.put(f"{SUPERSET_URL}/api/v1/chart/{existing['id']}",
                            json=payload, timeout=60)
            cid = existing["id"]
        else:
            r = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=payload, timeout=60)
            body = r.json()
            cid = body.get("id") or body.get("result", {}).get("id")
        if r.status_code not in (200, 201):
            raise RuntimeError(f"save chart '{spec['name']}' failed {r.status_code}: {r.text[:400]}")
        ids[spec["name"]] = cid
    return ids


def build_position_json(chart_ids):
    pos = {"DASHBOARD_VERSION_KEY": "v2"}
    pos["HEADER_ID"] = {"id": "HEADER_ID", "type": "HEADER", "meta": {}}
    grid_children = []
    items = list(chart_ids.items())
    row_idx = 0
    for i in range(0, len(items), 2):
        row_id = f"ROW-{row_idx}-{uuid.uuid4().hex[:8]}"
        row_idx += 1
        cell_children = []
        for name, cid in items[i:i + 2]:
            chart_key = f"CHART-{uuid.uuid4().hex[:8]}"
            pos[chart_key] = {
                "id": chart_key, "type": "CHART", "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {"chartId": cid, "sliceName": name, "width": 6, "height": 50},
            }
            cell_children.append(chart_key)
        pos[row_id] = {"id": row_id, "type": "ROW", "children": cell_children,
                       "parents": ["ROOT_ID", "GRID_ID"],
                       "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        grid_children.append(row_id)
    pos["GRID_ID"] = {"id": "GRID_ID", "type": "GRID", "children": grid_children,
                      "parents": ["ROOT_ID"]}
    pos["ROOT_ID"] = {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]}
    return pos


def ensure_dashboard(chart_ids):
    title = "Job Portal BI"
    slug = "job-portal-bi"
    payload = {
        "dashboard_title": title,
        "slug": slug,
        "published": True,
        "position_json": json.dumps(build_position_json(chart_ids)),
    }
    r = session.get(f"{SUPERSET_URL}/api/v1/dashboard/?q=(page_size:200)", timeout=30)
    r.raise_for_status()
    existing = None
    for item in r.json().get("result", []):
        if item.get("slug") == slug or item.get("dashboard_title") == title:
            existing = item
            break
    if existing:
        r = session.put(f"{SUPERSET_URL}/api/v1/dashboard/{existing['id']}",
                        json=payload, timeout=60)
        did = existing["id"]
    else:
        r = session.post(f"{SUPERSET_URL}/api/v1/dashboard/", json=payload, timeout=60)
        body = r.json()
        did = body.get("id") or body.get("result", {}).get("id")
    if r.status_code not in (200, 201):
        raise RuntimeError(f"save dashboard failed {r.status_code}: {r.text[:400]}")
    return did


def link_dashboard_charts(dash_id, chart_ids):
    """Populate dashboard_slices directly (not exposed by the Superset 6.x API).

    Idempotent via INSERT OR IGNORE. Skipped if the metadata DB isn't reachable.
    """
    if not os.path.exists(SUPERSET_DB_PATH):
        print(f"[superset] WARN metadata DB not found at {SUPERSET_DB_PATH}; "
              f"skipping dashboard<->chart link")
        return False
    conn = sqlite3.connect(SUPERSET_DB_PATH, timeout=30)
    try:
        cur = conn.cursor()
        for cid in chart_ids.values():
            cur.execute(
                "INSERT OR IGNORE INTO dashboard_slices (dashboard_id, slice_id) "
                "VALUES (?, ?)",
                (dash_id, cid),
            )
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM dashboard_slices WHERE dashboard_id=?", (dash_id,))
        n = cur.fetchone()[0]
        print(f"[superset] dashboard_slices linked: {n}")
        return True
    finally:
        conn.close()


def _unlink_chart(cid):
    if not os.path.exists(SUPERSET_DB_PATH):
        return
    conn = sqlite3.connect(SUPERSET_DB_PATH, timeout=30)
    try:
        conn.execute("DELETE FROM dashboard_slices WHERE slice_id=?", (cid,))
        conn.commit()
    finally:
        conn.close()


def prune_stale_charts():
    r = session.get(f"{SUPERSET_URL}/api/v1/chart/?q=(page_size:500)", timeout=30)
    r.raise_for_status()
    for item in r.json().get("result", []):
        if item.get("slice_name") not in STALE_CHART_NAMES:
            continue
        cid = item["id"]
        _unlink_chart(cid)
        d = session.delete(f"{SUPERSET_URL}/api/v1/chart/{cid}", timeout=60)
        if d.status_code not in (200, 204):
            print(f"[superset] WARN stale chart {cid} not deleted "
                  f"{d.status_code}: {d.text[:200]}")
        else:
            print(f"[superset] removed stale chart {cid} ({item['slice_name']})")


def main():
    _login()
    db_id = ensure_database()
    print(f"[superset] database id={db_id}")
    ds = {t: ensure_dataset(db_id, t) for t in DATASETS}
    print(f"[superset] datasets: {ds}")
    prune_stale_charts()
    chart_ids = ensure_charts(ds)
    print(f"[superset] charts: {len(chart_ids)} -> {chart_ids}")
    dash_id = ensure_dashboard(chart_ids)
    print(f"[superset] dashboard id={dash_id} slug=job-portal-bi")
    link_dashboard_charts(dash_id, chart_ids)
    print(f"[superset] open {SUPERSET_URL}/superset/dashboard/job-portal-bi/")


if __name__ == "__main__":
    main()
