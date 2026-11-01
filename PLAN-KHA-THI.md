# Plan khả thi: Nền tảng kết nối tuyển dụng thông minh (BI + AI)

Lập ngày 2026-11-01. Plan này thay phần thi công của `PLAN-BI-AI-JOB-SYSTEM.md` và `PLAN-DELTA-VOI-CODE-CU.md`. Hai file cũ chỉ giữ làm tư liệu; agent **không cần đọc** chúng khi thi công.

Mục tiêu: đạt đủ 5 checklist và đủ các ý của đề bài, trong điều kiện **ngân sách token của agent có hạn**, chỉ có **Gemini free key**, và **không có GPU**. Plan không ràng buộc thời gian lịch.

---

## 0. Ràng buộc và quy tắc tiết kiệm token (agent bắt buộc tuân theo)

| Ràng buộc | Cách xử lý |
|---|---|
| Token agent có hạn | Chia thành 8 phiên nhỏ (Mục 2). Mỗi phiên chỉ đọc file ghi trong cột "Đọc" của phiên đó. Trạng thái giữa các phiên lưu ở `PROGRESS.md` |
| Không GPU, không mô hình mạnh | Dùng TF-IDF + scikit-learn. Không dùng sentence-transformers, torch hay pgvector |
| Chỉ có Gemini free key | Gemini chỉ phục vụ 1 tính năng phụ là gợi ý sửa CV. Có cache và fallback. Hệ thống chạy đủ khi không có key |
| Tối thiểu việc thủ công | Người làm chỉ cần: bật Docker; dán `GEMINI_API_KEY` vào `.env` nếu muốn |

### Quy tắc token

1. **Mở đầu mỗi phiên**: chỉ đọc `PROGRESS.md` và mục tương ứng của file plan này, không đọc cả file. Không quét toàn bộ repo. Không mở `node_modules`, `.next`, `package-lock.json`, `__pycache__`, `uploads`.
2. **Đọc theo đoạn**: file trên 150 dòng thì dùng grep tìm hàm cần, rồi đọc đúng khoảng dòng đó. Áp dụng cho `bootstrap_superset.py` (21 KB), `main.py` (350 dòng), `api.ts`.
3. **Viết mới thay vì sửa lớn**: file mới mỗi file dưới khoảng 250 dòng. Riêng `main.py`, tách router sang `backend/app/routers/*.py` thay vì vá nhiều chỗ.
4. **Output lệnh luôn rút gọn**:
   - `pytest -q 2>&1 | tail -15`
   - `docker compose logs --tail 30 <svc>`
   - `curl -s ... | head -c 800`
   - Dùng `npm run build 2>&1 | tail -30`, không bật `next dev` theo dõi log.
5. **Không dùng screenshot để kiểm tra**: kiểm tra API bằng curl/pytest, kiểm tra trang bằng `get_page_text`. Chỉ chụp ảnh **một lần ở cuối** Phiên 7 để làm minh chứng.
6. **Dev ngoài Docker**:
   - Chỉ Postgres (và Superset ở Phiên 6) chạy trong Docker.
   - Backend chạy bằng `python` của host (đã có sklearn 1.8 và pandas 2.3), frontend chạy `npm run build`.
   - Chỉ rebuild image ở cuối Phiên 1 và Phiên 8.
7. **Sinh dữ liệu và tài liệu bằng script**, không để agent tự viết tay số liệu:
   - ERD và bảng truy vết sinh từ `schema.sql` và `traceability.yaml`.
   - Báo cáo được render từ `metrics.json` theo template.
8. **Giới hạn vòng sửa lỗi**: cùng một lỗi mà sửa thất bại 2 lần thì áp dụng phương án cắt (cột "Cắt nếu kẹt"), ghi vào `PROGRESS.md`, rồi đi tiếp.
9. **Không gọi subagent hay fan-out**, không viết lại các tài liệu md cũ.
10. **Kết thúc mỗi phiên**: thêm tối đa 10 dòng vào `PROGRESS.md`, ghi đã xong gì, lệnh kiểm tra nào và kết quả ra sao, phần nào bị cắt, lỗi nào còn treo.

---

## 1. Kiến trúc

- **Service**: `postgres`, `backend` (FastAPI), `frontend` (Next.js), `superset` và `superset-init`. Bỏ `redis`, `worker`, `beat` cùng `celery_app.py` và `tasks.py`.
- **Tầng dữ liệu**: `backend/db/schema.sql` idempotent, do `seed_db.py` áp dụng khi khởi động. Dùng psycopg2 qua `db.py` có sẵn (đã có retry). Không dùng Alembic hay ORM.
- **Auth**: bảng `users`, mật khẩu băm bcrypt, JWT ký bằng `JWT_SECRET` (pyjwt). Token lưu trong localStorage như hiện tại.
- **ML**: scikit-learn, pandas, numpy, joblib, rapidfuzz. Mô hình lưu ở `backend/models/*.joblib`.
- **Quy tắc cứng**: Postgres là nguồn dữ liệu duy nhất. Backend không đọc file JSON làm dữ liệu nghiệp vụ. UI không tự tính điểm khớp.

### 1.1 Schema: 11 bảng và 4 view

| Bảng | Cột chính |
|---|---|
| `users` | id, email, password_hash, role (candidate/employer/admin), company_id |
| `company` | id, name, location, industry, size |
| `job_posting` | id, job_key (unique), company_id, title, category, location, level, exp_years_min, education, salary_min, salary_max, description, requirements, source (`vietjobs`/`synthetic`/`fixture`), status, posted_at |
| `skill` | id, name, aliases, type (tech/soft) |
| `job_skill` | job_id, skill_id, weight (1.0 bắt buộc, 0.5 ưu tiên) |
| `candidate` | id, user_id, full_name, major, gpa, exp_years, education, location, expected_salary, is_simulated |
| `candidate_skill` | candidate_id, skill_id, source (cv/manual) |
| `cv_document` | id, candidate_id, filename, raw_text, parsed_json, health_score, health_issues_json |
| `application` | id, candidate_id, job_id, status (applied/screening/interview/offer/rejected), match_score, source (recommend/search), applied_at, updated_at, is_simulated |
| `matching_result` | candidate_id, job_id, score, components_json, matched_skills, missing_skills, model_version, created_at |
| `cv_suggestion` | cv_id, job_id, content_json, source (gemini/fallback), created_at |

View phục vụ BI:
- `v_skill_supply_demand`: số ứng viên và số tin theo kỹ năng.
- `v_salary_by_segment`: lương p25/p50/p75 theo ngành, cấp bậc, địa điểm và tháng.
- `v_funnel`: số đơn theo trạng thái và nguồn.
- `v_match_vs_outcome`: tỷ lệ qua vòng theo khoảng điểm khớp.

---

## 2. Tám phiên thi công

Mức token mỗi phiên: S là nhỏ, M là vừa, L là lớn. Thứ tự là bắt buộc. Riêng Phiên 3 có thể làm bất kỳ lúc nào sau Phiên 2.

| # | Checklist | Đọc (chỉ những file này) | Việc | Kiểm tra hoàn thành | Token | Cắt nếu kẹt |
|---|---|---|---|---|---|---|
| 1 | Nền | `docker-compose.yml`, `requirements.txt`, `main.py` (grep), `seed_db.py`, `db.py` | Mục 3.1 | `docker compose up -d postgres` chạy; `pytest -q` chạy được (0 test cũng được); `GET /health` trả 200 | M | — |
| 2 | CL1 | `PROGRESS.md`, `data/skill_alias.csv`, `backend/tests/fixtures/jobs_10.json` | Mục 3.2: schema, ETL, dữ liệu | Script `scripts/check_counts.py` in ra: job ≥ 2000, candidate ≥ 300, application ≥ 1500, khoảng thời gian `posted_at` | M | Dùng dữ liệu tổng hợp |
| 3 | CL1 | `schema.sql` | Mục 3.3: tài liệu sinh bằng script | Có `docs/01-yeu-cau-va-thiet-ke.md` với ERD Mermaid và bảng truy vết | S | — |
| 4 | CL2 | `cv_parser.py` | Mục 3.4: CV parser và CV health | `pytest -q tests/test_cv*.py` xanh | M | Bỏ tách đồ án |
| 5 | CL2 | `matching.py`, `PROGRESS.md` | Mục 3.5: matching, mô hình học, mô hình lương, API | `python -m ml.train_match` và `python -m ml.train_salary` chạy xong; curl 4 endpoint chính trả 200 | L | Bỏ mô hình lương; nếu LR kém thì giữ heuristic làm mặc định |
| 6 | CL3 | `bootstrap_superset.py` (grep các hàm `ensure_*`, `build_query_context`, danh sách chart) | Mục 3.6: BI | Bootstrap in bảng xác nhận mọi chart trả ≥ 1 hàng; `/api/v1/employer/kpi` trả 200 | M | Giảm còn 8 chart |
| 7 | CL4 | `lib/api.ts`, từng `page.tsx` cần sửa (grep `mock`) | Mục 3.7: Frontend | `npm run build` thành công; `get_page_text` của các trang trong luồng vàng có dữ liệu thật; 8 ảnh chụp trong `docs/qa/` | L | Bỏ `/saved` và trang admin |
| 8 | CL5 | `PROGRESS.md`, `reports/metrics.json` | Mục 3.8: test, đánh giá, báo cáo | `pytest -q` xanh; có `docs/bao-cao-danh-gia.md` và `.docx`; `docker compose up` toàn bộ chạy được | M | Bỏ bản docx |

---

## 3. Chi tiết

### 3.1 Phiên 1: Dọn nền

- Xoá `redis`, `worker`, `beat` khỏi compose. Xoá `celery_app.py`, `tasks.py`, `celerybeat-schedule` và `REDIS_URL`.
- `requirements.txt`: gỡ `celery` và `redis`. Thêm `scikit-learn`, `pandas`, `numpy`, `joblib`, `rapidfuzz`, `bcrypt`, `pyjwt`, `google-genai`, `pytest`, `huggingface_hub`.
- Sửa 4 lỗi:
  1. Upload bị path traversal: đặt tên file bằng uuid, chỉ nhận pdf và docx.
  2. Bỏ `DELETE FROM job_skills`.
  3. Bỏ khối code đọc `frontend/mock` trong `main.py`.
  4. UI không tự tính điểm (phần UI sửa ở Phiên 7).
- Chuyển `frontend/mock/jobs.json` thành `backend/tests/fixtures/jobs_10.json`.
- Tách `main.py` thành các router: `auth`, `jobs`, `cv`, `match`, `applications`, `employer`, `admin`.
- Tạo `PROGRESS.md`.

### 3.2 Phiên 2: Schema và dữ liệu

- Viết `schema.sql` theo Mục 1.1. Viết lại `seed_db.py` chỉ còn hai việc: áp dụng schema và gọi các hàm seed. Seed idempotent bằng `ON CONFLICT`.
- **Nguồn tin tuyển dụng**: thử lần lượt và dừng ở nguồn đầu tiên lấy được.
  1. `huggingface_hub` tải dataset VietJobs, không cần token. Giới hạn 5000 dòng.
  2. File CSV mẫu VietJobs trên GitHub.
  3. `etl/synth_jobs.py`: sinh khoảng 2000 tin từ fixture cùng `skill_alias.csv`, gồm 8 ngành, 6 tỉnh, 4 cấp bậc. Lương theo phân phối log-normal theo ngành và cấp bậc. `posted_at` rải đều 12 tháng. Mọi tin đặt `source='synthetic'`.
- `etl/load_jobs.py`:
  - Chuẩn hoá lương về đơn vị triệu VND/tháng.
  - Suy số năm kinh nghiệm và cấp bậc.
  - Tách kỹ năng bằng alias, khớp gần đúng bằng rapidfuzz với ngưỡng 90.
  - In ra khoảng thời gian `posted_at`. Nếu dữ liệu thật trải dưới 3 tháng, ghi vào `PROGRESS.md`; Phiên 6 sẽ đổi chart xu hướng lương thành lương theo cấp bậc và ngành.
- `etl/synth_candidates.py`: sinh 300–500 ứng viên với `is_simulated=true`. Kỹ năng lấy mẫu theo phân bố kỹ năng của các tin cùng ngành.
- `etl/synth_applications.py`:
  - Chạy **sau Phiên 5**, vì cần điểm khớp.
  - Mỗi ứng viên ứng tuyển 3–8 tin.
  - Xác suất qua từng vòng là `sigmoid(a*score + b)` cộng nhiễu, seed 42.
  - Ở Phiên 2 tạm dùng `skill_cov` làm điểm khớp, rồi chạy lại sau Phiên 5.
- Tạo 3 tài khoản demo (ứng viên, nhà tuyển dụng, admin) và ghi vào `ACCOUNTS.md`.
- Sinh 3 CV mẫu dạng docx bằng python-docx vào `data/sample_cvs/`. Mỗi CV có chất lượng khác nhau: tốt, trung bình, kém.

### 3.3 Phiên 3: Tài liệu checklist 1 (sinh bằng script)

- `docs/traceability.yaml`: agent viết tay, khoảng 20 FR và 6 NFR. Mỗi yêu cầu trỏ tới API, bảng, trang và test tương ứng.
- `scripts/gen_docs.py` ghép các phần sau thành `docs/01-yeu-cau-va-thiet-ke.md`:
  - Phần mô tả ngắn: bối cảnh, 3 vai trò, use case Mermaid.
  - ERD Mermaid, sinh tự động từ `schema.sql`.
  - Bảng FR, NFR và truy vết, sinh từ yaml.
  - Mục "Khác biệt so với thiết kế gốc": không dùng LinkedIn API, không dùng embedding, dữ liệu ứng viên là mô phỏng.

### 3.4 Phiên 4: Phân tích CV

- Giữ các hàm đọc PDF, DOCX và chuẩn hoá có sẵn. Thêm các hàm:
  - `split_sections`
  - `extract_contacts` (email, số điện thoại)
  - `extract_gpa`
  - `extract_education`
  - `extract_projects`
- Kết quả trả về theo JSON cố định: `{skills, exp_years, education, gpa, contacts, sections, projects}`.
- `ml/cv_health.py` chấm theo 6 luật. Mỗi luật có điểm và câu báo lỗi cụ thể:
  1. Đủ các mục.
  2. Có thông tin liên hệ.
  3. Có ít nhất 5 kỹ năng.
  4. Có số liệu định lượng.
  5. Độ dài hợp lý.
  6. Không dùng cụm sáo rỗng.
- Test: 8 case trên 3 CV mẫu. Điểm health phải xếp đúng thứ tự tốt > trung bình > kém.

### 3.5 Phiên 5: Matching Score và các mô hình

**Đặc trưng** (giá trị 0–1):

| Đặc trưng | Cách tính |
|---|---|
| `skill_cov` | Weighted coverage kỹ năng của JD |
| `text_sim` | Cosine TF-IDF (word 1–2gram + char 3–5gram). Vectorizer fit một lần trên toàn bộ JD, lưu joblib |
| `exp_fit` | Mức đáp ứng số năm kinh nghiệm |
| `edu_fit` | Mức đáp ứng trình độ học vấn |
| `loc_fit` | Mức khớp địa điểm |
| `salary_fit` | Mức khớp lương mong muốn với dải lương của tin |

**Mô hình:**
- `heuristic-v1`: tổng có trọng số cố định.
- `lr-v1`: `LogisticRegression` học trên nhãn yếu, lấy `predict_proba` làm điểm. Hệ số của mô hình dùng để giải thích.

**Nhãn yếu, có chống vòng lặp:**
- Mẫu dương: lấy 50–80% kỹ năng của JD, thêm 1–3 kỹ năng nhiễu, kinh nghiệm lệch ±1 năm.
- Mẫu âm khó: tin cùng ngành nhưng khác cấp bậc, hoặc trùng dưới 30% kỹ năng.
- Mẫu âm dễ: tin khác ngành.
- **Chia train/test theo ngành**: 6 ngành để train, 2 ngành để test.

**Phần còn lại:**
- Giải thích bằng câu sinh từ các thành phần, kèm kỹ năng thiếu xếp theo độ phổ biến trong ngành. Ngưỡng hiển thị: từ 0.75 là cao, 0.55–0.75 là trung bình, dưới 0.55 là thấp.
- Tính điểm theo lô bằng numpy khi hồ sơ thay đổi, ghi vào `matching_result`.
- **Mô hình lương** `ml/train_salary.py`:
  - So sánh RandomForest với baseline trung vị theo phân khúc, chia dữ liệu theo hash `job_key`.
  - Đo MAE và MAPE.
  - API trả về dải p25–p75 thực tế và kết quả dự đoán của mô hình.
- **Gemini** (`ml/cv_suggest.py`):
  - Chỉ gọi khi người dùng bấm nút.
  - Prompt yêu cầu trả JSON gồm `summary`, `add_keywords`, `rewrite_bullets`, `priority_fixes`.
  - Cache vào `cv_suggestion`, timeout 15 giây.
  - Khi thiếu key, hết quota hoặc lỗi thì dùng fallback template dựng từ kỹ năng thiếu cùng CV health. Kết quả mang `source=fallback`.
  - Model: model flash có trong free tier tại thời điểm chạy. Đọc tên model từ biến `GEMINI_MODEL`, mặc định `gemini-2.5-flash`.

**API:**

| Endpoint | Mô tả |
|---|---|
| `POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `GET /api/v1/users/me` | Đăng nhập, đăng ký, thông tin người dùng |
| `GET /api/v1/jobs` | Tìm kiếm và lọc theo từ khoá (ILIKE), ngành, địa điểm, cấp bậc, có phân trang; mỗi tin kèm điểm khớp nếu đã đăng nhập |
| `GET /api/v1/jobs/{id}` | Chi tiết tin |
| `PUT /api/v1/candidate/profile` | Cập nhật hồ sơ ứng viên |
| `POST /api/v1/cv/upload` | Parse CV, chấm health, cập nhật kỹ năng, tính lại matching |
| `GET /api/v1/recommendations?k=20` | Danh sách gợi ý |
| `GET /api/v1/jobs/{id}/match` | Thành phần điểm, kỹ năng thiếu, giải thích |
| `POST /api/v1/cv/suggest?job_id=` | Gợi ý sửa CV theo tin |
| `GET /api/v1/salary/estimate` | Ước lượng lương |
| `POST /api/v1/applications`, `GET /api/v1/applications` | Ứng tuyển và xem đơn |
| `GET /api/v1/employer/jobs`, `POST /api/v1/employer/jobs` | Quản lý tin của nhà tuyển dụng |
| `GET /api/v1/employer/jobs/{id}/candidates` | Ứng viên xếp theo điểm, lọc theo kỹ năng thiếu |
| `PATCH /api/v1/applications/{id}` | Nhà tuyển dụng đổi trạng thái đơn |
| `GET /api/v1/employer/kpi` | KPI lọc theo `company_id` của token |
| `GET /api/v1/market/stats` | Số liệu thị trường cho trang BI trong app |

### 3.6 Phiên 6: BI

Mở rộng `bootstrap_superset.py`, giữ nguyên các helper đã chạy. Dựng 2 dashboard.

**Dashboard A: Thị trường lao động**

| Loại | Chart |
|---|---|
| Bắt buộc | (1) Số ứng viên theo kỹ năng, top 15, đặt cạnh số tin cần kỹ năng đó |
| Bắt buộc | (2) Xu hướng lương p25/p50/p75 theo tháng và theo ngành (hoặc theo cấp bậc nếu dữ liệu ít tháng) |
| Đề xuất | Chỉ số khan hiếm kỹ năng (cầu chia cung) |
| Đề xuất | Kỹ năng tăng hoặc giảm nhanh nhất giữa hai quý gần nhất |
| Đề xuất | Số tin theo ngành và theo địa điểm |
| Đề xuất | Chênh lệch lương theo kỹ năng so với trung vị ngành |
| Đề xuất | Tỷ lệ tin công khai mức lương |

**Dashboard B: Tuyển dụng**

| Loại | Chart |
|---|---|
| Bắt buộc | (3) Tỷ lệ chuyển đổi: funnel applied → screening → interview → offer, chia theo nguồn (gợi ý hay tìm kiếm) |
| Đề xuất | Phân bố Matching Score |
| Đề xuất | Tỷ lệ qua vòng theo khoảng điểm (kiểm tra hiệu chuẩn) |
| Đề xuất | Thời gian trung bình đến khi có phản hồi |
| Đề xuất | Số đơn theo tuần |

- Chart nào dùng dữ liệu mô phỏng thì tiêu đề có chữ "(mô phỏng)".
- **BI cho nhà tuyển dụng trong app**: trang `/employer/dashboard` hiển thị 4 thẻ KPI, funnel và top kỹ năng thiếu của ứng viên. Dữ liệu lấy từ `/employer/kpi`, đã lọc theo công ty. Biểu đồ vẽ bằng thẻ div/SVG đơn giản, không thêm thư viện. Có link mở Superset.

### 3.7 Phiên 7: Frontend

| Trang | Việc |
|---|---|
| `lib/api.ts` | Viết lại theo các endpoint ở Mục 3.5 |
| `/jobs` | Gọi API thay mock, có bộ lọc, mỗi tin có badge điểm khớp |
| `/jobs/[id]` | Hiển thị các thành phần điểm, kỹ năng thiếu, ước lượng lương, nút Ứng tuyển, nút "Gợi ý sửa CV (AI)" kèm nhãn nguồn gemini/offline |
| `/recommendations` | Gọi API, có lý do khớp |
| `/profile` | Form hồ sơ, tải CV lên, kỹ năng trích được, điểm health kèm danh sách lỗi |
| `/applications` | Danh sách đơn và trạng thái |
| `/employer/jobs` (mới) | Danh sách tin và form tạo tin |
| `/employer/candidates` (mới) | Ứng viên xếp hạng, đổi trạng thái đơn |
| `/employer/dashboard` (mới) | KPI như Mục 3.6 |
| `/admin/dashboard` | Số bản ghi, `SEED_MODE`, nguồn dữ liệu |
| `/`, `/saved` | Bỏ import mock |

- Kiểm tra từng trang bằng `get_page_text`.
- Ở cuối phiên, chụp 8 ảnh của luồng vàng lưu vào `docs/qa/`: đăng nhập → tải CV → gợi ý → chi tiết tin → gợi ý sửa CV → ứng tuyển → nhà tuyển dụng xem ứng viên xếp hạng → dashboard.

### 3.8 Phiên 8: Kiểm thử và báo cáo

- **pytest**, khoảng 20 test:
  - Parser và CV health.
  - Từng đặc trưng matching.
  - Tính tất định của điểm.
  - Chuẩn hoá lương.
  - API smoke.
  - Phân quyền: nhà tuyển dụng A không xem được dữ liệu của B.
  - Fallback Gemini.
  - Kiểm tra chất lượng dữ liệu bằng SQL: thiếu trường, trùng `job_key`, lương âm, kỹ năng mồ côi.
- **`python -m ml.evaluate`** xuất `reports/metrics.json`:
  - So sánh 5 phương pháp trên tập test: ngẫu nhiên, chỉ TF-IDF, chỉ `skill_cov`, `heuristic-v1`, `lr-v1`.
  - Metric: P@5, Recall@10, MRR, nDCG@10, mỗi metric có khoảng tin cậy bootstrap 95%.
  - Độ nhạy của điểm khi thêm hoặc bớt 1 kỹ năng.
  - Độ trễ p50/p95 của các endpoint gợi ý, đo bằng 100 request.
  - MAE/MAPE của mô hình lương so với baseline.
  - Tỷ lệ qua vòng của nhóm điểm ≥ 0.75 so với nhóm < 0.55 (mô phỏng).
- **Nhãn tay, tuỳ chọn**: xuất `reports/label_me.csv` gồm 20 cặp. Nếu người làm điền thì tính Spearman; nếu không thì báo cáo ghi rõ chưa kiểm chứng bằng người.
- **Báo cáo**: `scripts/gen_report.py` render `docs/bao-cao-danh-gia.md` từ template và `metrics.json`, nên số liệu khớp tuyệt đối. Agent chỉ viết phần nhận xét và 3 ví dụ mô hình sai. Bản `.docx` sinh bằng python-docx. Nội dung báo cáo:
  - Phương pháp.
  - Dữ liệu, tách rõ phần thật và phần mô phỏng.
  - Bảng kết quả.
  - So sánh với 4 mục tiêu của slide 10.
  - Phân tích lỗi.
  - Hạn chế.
  - Hướng phát triển.

---

## 4. Đối chiếu với đề bài

| Ý của đề bài / checklist | Đáp ứng bởi |
|---|---|
| AI tự động khớp kỹ năng với yêu cầu công việc (Matching Score) | Mục 3.5: 6 đặc trưng, LR học từ dữ liệu, có giải thích |
| Phân tích CV | Mục 3.4: parser, CV health; Gemini gợi ý sửa CV |
| BI phân tích xu hướng thị trường lao động | Dashboard A |
| Báo cáo trực quan cho nhà tuyển dụng | Dashboard B, `/employer/dashboard` lọc theo công ty |
| Tối ưu hoá quy trình tìm việc | Tìm kiếm, lọc, gợi ý top-K, gợi ý sửa CV |
| Nâng cao độ chính xác tuyển dụng | Xếp hạng ứng viên cho nhà tuyển dụng, đánh giá P@k/nDCG so với các baseline |
| CL1: CSDL cho ứng viên, nhà tuyển dụng, tin | Mục 1.1, 3.2, 3.3 |
| CL2: AI/ML phân tích CV và tính điểm tương thích | Mục 3.4, 3.5 |
| CL3: ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi, cộng chỉ số đề xuất | Mục 3.6: 3 chỉ số bắt buộc và 9 chỉ số đề xuất |
| CL4: Frontend và tích hợp API AI/BI | Mục 3.7 |
| CL5: Kiểm thử với dữ liệu mẫu và báo cáo hiệu quả gợi ý | Mục 3.8 |

## 5. Việc người làm phải tự làm

1. Bật Docker Desktop trước Phiên 1.
2. (Tuỳ chọn) Dán `GEMINI_API_KEY` vào `.env`.
3. (Tuỳ chọn) Điền `reports/label_me.csv`.
4. Mở phiên mới cho từng phiên thi công với câu lệnh: "Thực hiện Phiên N theo PLAN-KHA-THI.md, đọc PROGRESS.md trước".

## 6. Rủi ro

| Rủi ro | Dự phòng |
|---|---|
| VietJobs cần token hoặc tải lỗi | Dùng dữ liệu tổng hợp; báo cáo ghi rõ nguồn |
| Build Superset lỗi | Superset đã từng chạy được. Nếu vẫn hỏng thì `/employer/dashboard` cùng `/market/stats` vẫn phủ được 3 chỉ số bắt buộc |
| `lr-v1` không tốt hơn heuristic | Báo cáo trung thực; chọn mô hình tốt hơn làm mặc định |
| Hết token giữa phiên | `PROGRESS.md` cho phép phiên sau làm tiếp mà không phải khám phá lại |
| Gemini hết quota | Fallback template, có nhãn hiển thị rõ |

## 7. Ngoài phạm vi (ghi vào "Hướng phát triển")

Embedding và pgvector, skill graph PMI, quét ATS trực tiếp, lập lịch ETL, Alembic, cookie httpOnly, audit log, nhúng Superset bằng guest token, RAG đầy đủ, E2E tự động và load test song song.
