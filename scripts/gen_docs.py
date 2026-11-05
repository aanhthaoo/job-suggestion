"""Generate docs/01-yeu-cau-va-thiet-ke.md from backend/db/schema.sql + docs/traceability.yaml.

Usage: python scripts/gen_docs.py
ERD and traceability tables are derived, never hand-written, so they cannot drift from the code.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "backend" / "db" / "schema.sql"
TRACE = ROOT / "docs" / "traceability.yaml"
OUT = ROOT / "docs" / "01-yeu-cau-va-thiet-ke.md"

INTRO = """# Yêu cầu và thiết kế hệ thống

> File này được sinh tự động bởi `scripts/gen_docs.py` từ `backend/db/schema.sql` và `docs/traceability.yaml`. Không sửa tay.

## 1. Bối cảnh và mục tiêu

Nền tảng kết nối tuyển dụng thông minh kết hợp BI và AI. Hệ thống (1) tự động khớp kỹ năng trong CV với yêu cầu của tin
tuyển dụng thành một điểm Matching Score có giải thích, (2) phân tích CV và chấm sức khoẻ CV, (3) cung cấp dashboard BI
về thị trường lao động cho quản trị viên và về hiệu quả tuyển dụng cho nhà tuyển dụng, (4) tối ưu quy trình tìm việc
bằng tìm kiếm, lọc, gợi ý top-K và gợi ý sửa CV.

## 2. Vai trò và use case

| Vai trò | Mô tả |
|---|---|
| Ứng viên (`candidate`) | Tạo hồ sơ, tải CV, xem gợi ý việc làm, ứng tuyển |
| Nhà tuyển dụng (`employer`) | Đăng tin, xem ứng viên xếp hạng theo điểm khớp, đổi trạng thái đơn, xem KPI công ty mình |
| Quản trị (`admin`) | Xem dashboard thị trường và tuyển dụng, theo dõi dữ liệu hệ thống |

```mermaid
flowchart LR
  C([Ứng viên]) --> UC1[Đăng ký / đăng nhập]
  C --> UC2[Tìm kiếm và lọc tin]
  C --> UC3[Tải CV và xem điểm sức khoẻ CV]
  C --> UC4[Xem gợi ý và giải thích điểm khớp]
  C --> UC5[Gợi ý sửa CV theo tin]
  C --> UC6[Ứng tuyển]
  E([Nhà tuyển dụng]) --> UC7[Đăng và quản lý tin]
  E --> UC8[Xem ứng viên xếp hạng]
  E --> UC9[Đổi trạng thái đơn]
  E --> UC10[Xem KPI tuyển dụng của công ty]
  A([Quản trị]) --> UC11[Dashboard thị trường lao động]
  A --> UC12[Dashboard tuyển dụng]
  A --> UC13[Theo dõi dữ liệu hệ thống]
```

## 3. Kiến trúc

Service: `postgres`, `backend` (FastAPI), `frontend` (Next.js), `superset`. Postgres là nguồn dữ liệu duy nhất; schema áp
dụng idempotent khi backend khởi động. ML dùng scikit-learn (TF-IDF, hồi quy logistic, random forest), không cần GPU.
Gemini chỉ phục vụ tính năng gợi ý sửa CV, có cache và fallback offline.

"""

DIFF = """
## 6. Khác biệt so với thiết kế gốc

| Thiết kế gốc | Thực tế | Lý do |
|---|---|---|
| Lấy tin qua LinkedIn API / quét ATS | Dataset VietJobs công khai (HuggingFace), mẫu tối đa 5000 dòng | Không có quyền truy cập API; VietJobs là tin thật |
| Embedding + pgvector | TF-IDF + đặc trưng kỹ năng, hồi quy logistic | Không có GPU, tiết kiệm tài nguyên, dễ giải thích |
| Dữ liệu ứng viên thật | Ứng viên và đơn ứng tuyển mô phỏng (`is_simulated=true`) | Không có dữ liệu ứng viên công khai |
| Ngày đăng tin thật | `posted_at` mô phỏng (rải đều 12 tháng, seed 42); VietJobs không có cột ngày | Cần trục thời gian cho xu hướng lương; ghi rõ trong báo cáo |
| Công ty tuyển dụng thật | Công ty mô phỏng gán theo ngành | VietJobs không có cột công ty |
| Celery + Redis cho ETL định kỳ | Bỏ; ETL chạy tay bằng `python -m etl.load_jobs` | Giảm số service, không cần lập lịch trong phạm vi đồ án |
"""


def parse_tables(sql: str):
    tables = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", sql, re.S):
        name, body = m.group(1), m.group(2)
        cols, fks = [], []
        for line in body.split("\n"):
            line = line.strip().rstrip(",")
            if not line or line.startswith("--") or line.upper().startswith(("PRIMARY KEY", "UNIQUE")):
                continue
            parts = line.split()
            col, typ = parts[0], parts[1].split("(")[0]
            tags = []
            if "PRIMARY KEY" in line.upper():
                tags.append("PK")
            ref = re.search(r"REFERENCES (\w+)\(", line)
            if ref:
                tags.append("FK")
                fks.append((col, ref.group(1)))
            cols.append((typ, col, " ".join(tags)))
        pk = re.search(r"PRIMARY KEY \(([^)]*)\)", body)
        if pk:
            cols = [(t, c, ("PK" if c in [x.strip() for x in pk.group(1).split(",")] and "PK" not in g else g).strip())
                    for t, c, g in cols]
        tables[name] = {"cols": cols, "fks": fks}
    return tables


def erd(tables) -> str:
    out = ["```mermaid", "erDiagram"]
    for name, t in tables.items():
        out.append(f"  {name} {{")
        for typ, col, tag in t["cols"]:
            out.append(f"    {typ.lower()} {col}" + (f" {tag.replace(' ', ',')}" if tag else ""))
        out.append("  }")
    for name, t in tables.items():
        for col, ref in t["fks"]:
            out.append(f"  {ref} ||--o{{ {name} : \"{col}\"")
    out.append("```")
    return "\n".join(out)


def views(sql: str):
    return re.findall(r"CREATE OR REPLACE VIEW (\w+)", sql)


def trace_tables(data) -> str:
    def row(r, cols):
        return "| " + " | ".join(str(r.get(c, "-")).replace("|", "/") if not isinstance(r.get(c), list)
                                  else ", ".join(r[c]) for c in cols) + " |"
    out = []
    for key, title in (("functional", "Yêu cầu chức năng (FR)"), ("non_functional", "Yêu cầu phi chức năng (NFR)")):
        cols = ["id", "title", "role", "api", "tables", "page", "test", "status"]
        cols = [c for c in cols if any(c in r for r in data[key])]
        out.append(f"### {title}\n")
        out.append("| " + " | ".join(cols) + " |")
        out.append("|" + "---|" * len(cols))
        out += [row(r, cols) for r in data[key]]
        out.append("")
    allr = data["functional"] + data["non_functional"]
    done = sum(1 for r in allr if r["status"] == "done")
    out.append(f"Tiến độ: **{done}/{len(allr)}** yêu cầu đã hoàn thành, còn lại ở trạng thái `planned` "
               f"(phiên thi công ghi ở cột `phase` của `docs/traceability.yaml`).\n")
    return "\n".join(out)


def main():
    sql = SCHEMA.read_text(encoding="utf-8")
    tables = parse_tables(sql)
    data = yaml.safe_load(TRACE.read_text(encoding="utf-8"))
    parts = [INTRO,
             f"## 4. Thiết kế dữ liệu\n\nSchema gồm **{len(tables)} bảng** và **{len(views(sql))} view** phục vụ BI "
             f"({', '.join('`' + v + '`' for v in views(sql))}). Đơn vị lương: triệu VND/tháng. "
             f"`application.stage_reached` (0 nộp, 1 sàng lọc, 2 phỏng vấn, 3 offer) dùng cho funnel.\n",
             erd(tables), "\n## 5. Truy vết yêu cầu\n", trace_tables(data), DIFF]
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(tables)} tables, {len(views(sql))} views, "
          f"{len(data['functional'])} FR, {len(data['non_functional'])} NFR")


if __name__ == "__main__":
    sys.exit(main())
