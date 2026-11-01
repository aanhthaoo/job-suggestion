# Delta plan: đối chiếu `PLAN-BI-AI-JOB-SYSTEM.md` với code đang có

Đọc kèm file plan chính. File này trả lời câu hỏi: từ kho code hiện tại ở `job-suggestion/`, cái gì giữ, cái gì mở rộng, cái gì viết lại, cái gì phải bỏ, và thứ tự thi công tối ưu để không phải làm lại thứ đã chạy được.

Kiểm kê ngày 2026-10-28 trên 40 file nguồn (backend 8 file, frontend 12 trang và 4 module, superset 3 file, docker-compose, data). Không có file test, không có Alembic, không có CI.

Quy ước: **GIỮ** gần như nguyên, **MỞ RỘNG** giữ khung và thêm phần thiếu, **VIẾT LẠI** khung hiện tại không đi được tới yêu cầu, **BỎ** là code phải xoá hoặc chuyển vai trò.

---

## 1. Kết luận tổng quan

| Khu vực | Mức reuse được | Ghi chú |
|---|---|---|
| Hạ tầng Docker và Superset plumbing | Khoảng 75% | Postgres pgvector, Superset 6.1 có psycopg2, bootstrap REST một phát ăn ngay, toàn bộ kiêng kỵ đã được mã hoá thành code chạy được |
| CV parser | Khoảng 35% | Đọc PDF/DOCX và khớp alias đã xong; thiếu sections, GPA, đồ án, điểm sức khoẻ CV, lưu DB |
| Matching | Khoảng 30% | Khung tính điểm và giải thích đã có nhưng Jaccard union, 3 thành phần, không học trọng số, không ngữ nghĩa, không bền hoá kết quả |
| ETL ingestion | Khoảng 10% | `tasks.py` có khung Celery nhưng thân hàm là `pass`, không ghi một dòng nào xuống DB |
| Schema và tầng dữ liệu | Khoảng 20% | 5 bảng demo trái với 20 bảng trong plan; pattern idempotent và connect-retry thì rất đáng giữ |
| Frontend | Khoảng 40% | 12 trang, design system và điều hướng đã đủ hình hài; 8 trang trong đó đang binding sai nguồn dữ liệu |
| BI dashboard | Khoảng 50% | 13 chart chạy được, nhưng mới phủ 3 trong 15 chỉ số plan yêu cầu và chưa chia 3 dashboard theo vai trò |
| ML mô hình lương và embedding | 0% | Chưa có gì, requirements.txt cũng chưa khai các thư viện |
| Kiểm thử | 0% | Không tồn tại |

Tỷ trọng chung: hạ tầng và một phần Superset cùng parser reuse được nhiều; toàn bộ phần AI/ML, ETL thật, kiểm thử và báo cáo là làm mới. Ước tính khối lượng còn lại khoảng 65% so với plan gốc, đổi lại P0 của plan (dựng hạ tầng) gần như đã xong và đã được kiểm chứng bằng chạy thật.

---

## 2. Hiện trạng theo từng file, kèm lỗi phải sửa khi mở rộng

| File | Dòng | Trạng thái thật |
|---|---|---|
| [backend/app/main.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/main.py) | 350 | Không đụng tới Postgres. Nguồn dữ liệu là `frontend/mock/jobs.json` (10 tin) nạp vào RAM ở dòng 48. `MOCK_USERS` là dict in-memory dòng 101, token giả `"mock-jwt-token-" + user.id` dòng 115, mật khẩu so plaintext dòng 110. `/applications`, `/saved-jobs`, `/admin/stats`, `/admin/tasks` trả dữ liệu rỗng hoặc cứng (dòng 196-250). `/api/v1/match/calculate` và `/api/v1/recommendations` nhận profile qua body và query params nên chỉ đúng cho demo, không đọc hồ sơ đã lưu. `/api/v1/cv/parse` dòng 314 có thật nhưng không ghi DB và không có trang UI nào gọi |
| [backend/app/matching.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/matching.py) | 153 | Trọng số cố định 0.40 kỹ năng, 0.35 kinh nghiệm, 0.25 địa điểm ở dòng 84. `calculate_skill_overlap` dùng Jaccard trên union (dòng 22) nên hồ sơ càng có nhiều kỹ năng thì càng bị phạt, ngược bản chất khớp yêu cầu công việc. Không có thành phần trình độ, lương, ngữ nghĩa. Không có `model_version`. Có sẵn `get_recommendation` chia ngưỡng 0.75 và 0.60 và matched và missing skills, phần này khớp plan nên giữ |
| [backend/app/cv_parser.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/cv_parser.py) | 243 | Chuẩn hoá Unicode NFC,PyMuPDF và python-docx, khớp alias bằng word-boundary regex, regex kinh nghiệm và bằng cấp (dòng 153-187). Thiếu hoàn toàn: tách section, GPA, tên trường, năm tốt nghiệp, chứng chỉ, điện thoại và email, chấm điểm sức khoẻ CV, độ sâu đồ án, output JSON schema. Danh sách alias dự phòng hard-code 38 kỹ năng ngay trong hàm dòng 19-58 |
| [backend/app/seed_db.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/seed_db.py) | 196 | Pattern tốt: schema idempotent, upsert ON CONFLICT, 15 hồ sơ và 120 đơn ứng tuyển sinh ngẫu nhiên có seed 42 để BI có chuỗi thời gian. Vấn đề: dòng 134 `DELETE FROM job_skills` rồi mới chèn lại mỗi lần khởi động, nên mọi cột mở rộng như `required`, `weight`, `mention_count` vừa ghi sẽ bị xoá sạch. Chỉ tạo 5 bảng |
| [backend/app/tasks.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/tasks.py) | 163 | 4 task Celery, cả 4 thân hàm là `pass` hoặc chú thích "In production". `reconcile_jobs` chỉ trả về JSON thành công giả. `company_tokens` hard-code 1 token `navervietnam` |
| [backend/app/db.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/app/db.py) | 32 | Giữ nguyên: connect psycopg2 với retry 30 lần, chờ Postgres khởi động, rất hợp với compose |
| [backend/requirements.txt](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/backend/requirements.txt) | 13 gói | **Thiếu toàn bộ ML**: không có scikit-learn, numpy, pandas, sentence-transformers, rapidfuzz, huggingface-hub, google-genai. Máy host đã cài sẵn scikit-learn 1.8.0 và pandas nên chạy tay được, nhưng build container sẽ không có. Python 3.11-slim trong khi host dùng 3.12 |
| [superset/bootstrap_superset.py](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/superset/bootstrap_superset.py) | 21 KB | Đây là tài sản lớn nhất. Đã giải quyết xong login CSRF, ensure database, ensure dataset, `build_query_context`, pie dùng `metric` số ít, trend dùng `__timestamp` và `time_grain_sqla`, `table_timestamp` cho viz table, ghi `dashboard_slices` trực tiếp sqlite, `prune_stale_charts`. 13 chart đang phủ: 2 chỉ số lớn, việc làm theo địa điểm, ứng tuyển theo trạng thái, kỹ năng top 15, 2 pie, ứng tuyển theo tuần, xu hướng theo trạng thái, việc đăng theo tuần, tỷ lệ trúng tuyển theo tuần, lương trung bình theo địa điểm, bảng chi tiết |
| [docker-compose.yml](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/docker-compose.yml) | 162 | 7 service, trong đó `worker` và `beat` đang chạy Celery cho các task rỗng. `superset-init` one-shot là mảnh ghép khó, đã hoạt động |
| [frontend/app/recommendations/page.tsx](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/frontend/app/recommendations/page.tsx) | 151 | Dòng 42 tới 55 tính điểm trong trình duyệt trên `MOCK_JOBS`, công thức là `matched / jobSkills.size` tức **coverage**, khác công thức Jaccard union ở backend. Trang này gọi API `/recommendations` sẽ cho ra con số khác với con số đang hiển thị |
| [frontend/lib/api.ts](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/frontend/lib/api.ts) | 237 | `uploadCV` dòng 194 gọi `/users/me/cv/upload` và `getCVs` dòng 209 gọi `/users/me/cvs`, **hai endpoint này không tồn tại trong backend**; backend chỉ có `POST /cv/parse`. Token lưu localStorage, không phải httpOnly cookie |
| 8 trang import `mock/jobs.json` | - | `page.tsx`, `jobs/page.tsx`, `jobs/[id]/page.tsx`, `saved/page.tsx`, `applications/page.tsx`, `profile/page.tsx`, `recommendations/page.tsx`, `admin/dashboard/page.tsx`. Chỉ `login`, `register`, `admin/dashboard` là gọi API thật |
| [frontend/package.json](file:///D:/individual/tlu%20document/business%20intelligence%20system/btap5-job/job-suggestion/frontend/package.json) | - | Next 16.4, React 19.3, tailwind, react-query và zustand và zod đã cài nhưng chưa dùng ở các trang. **Không có thư viện vẽ biểu đồ**, nên KPI nhúng trong trang employer phải thêm recharts hoặc tự vẽ SVG |

Bốn lỗi phải sửa ngay vì ảnh hưởng tính đúng của số liệu và bảo mật:

1. `main.py` dòng 321 ghép `file.filename` thẳng vào đường dẫn lưu file, tên file dạng `../../x.pdf` thoát khỏi thư mục uploads. Sửa bằng `os.path.basename` và đổi tên thành uuid, chỉ accept pdf và docx.
2. `seed_db.py` dòng 134 xoá toàn bộ `job_skills` mỗi lần backend khởi động, sẽ làm mất dữ liệu chuẩn hoá mà ETL mới ghi vào.
3. Backend đọc mock từ `frontend/mock` qua ba lộ trình tìm kiếm (dòng 16-23), còn Postgres thì chỉ `seed_db` ghi vào; API và DB là **hai nguồn dữ liệu song song không bao giờ gặp nhau**. Dashboard Superset hiển thị số khác với số API trả về.
4. Hai điểm khớp về hình thức nhưng lệch về toán: `/recommendations` backend Jaccard union, UI coverage. Khi demo mà giảng viên bấm thử hai trang sẽ thấy hai điểm khác nhau cho cùng một hồ sơ.

---

## 3. Bảng delta theo từng checklist của plan

### Checklist 1, yêu cầu và CSDL

| Hạng mục plan | Code hiện có | Kết luận | Việc cụ thể |
|---|---|---|---|
| Tài liệu SRS, FR và NFR, bảng truy vết | 12 file markdown mô phỏng setup và kế hoạch cũ | MỚI | Viết `docs/01-yeu-cau-va-thiet-ke.md`, coi các file `IMPLEMENTATION_PLAN.md`, `PROJECT_SUMMARY.md` cũ là tư liệu, không tái sử dụng nội dung |
| ERD 20 bảng | `seed_db.py` có 5 bảng | MỞ RỘNG | Giữ pattern schema-in-python nhưng chuyển sang `backend/db/migrations/001_init.sql`, thêm `skill_taxonomy`, `occupation_graph`, `candidate`, `cv_document`, `candidate_skill`, `academic_project`, `matching_result`, `cv_outline_suggestion`, `recommendation_event`, `ingestion_run`, `data_quality_metric`, `audit_log`; `users` tách thành `users` cộng `candidate`; `companies` mở thành `company` có `ats_board`, `size`, `industry` |
| `job_posting` đủ cột nguồn và trạng thái | Bảng `jobs` 15 cột, `id TEXT` | VIẾT LẠI | Thêm `job_key` unique, `source`, `salary_source`, `category`, `qualifications`, `benefits`, `description` và `requirements_text` đã có, `first_seen_at`, `last_seen_at`, `status` giá trị open và closed, `embedding vector(384)`; đổi `id` sang BIGINT generated, giữ `job_key` làm khoá đối chiếu ETL |
| pgvector và FTS | Ảnh `pgvector/pgvector:pg16` đã đúng | MỞ RỘNG | Migration thêm `CREATE EXTENSION vector`, `tsvector` cộng index GIN, index HNSW; chưa từng bật extension nào |
| Tài khoản demo ba vai trò | `DEMO_USERS` 3 người trong `seed_db.py` dòng 72 | GIỮ | Giữ nguyên ba tài khoản, thêm hồ sơ kỹ năng và CV mẫu gắn với `u_user` |
| 120 đơn ứng tuyển ngẫu nhiên có seed | `seed_db.py` dòng 154-174 | MỞ RỘNG | Giữ cơ chế seed 42 làm **fallback offline** khi chưa tải được VietJobs, nhưng scale theo số ứng viên thật và trạng thái phải khớp funnel 5 bậc |

### Checklist 2, AI/ML

| Hạng mục plan | Code hiện có | Kết luận | Việc cụ thể |
|---|---|---|---|
| ETL VietJobs 48k | Không có | MỚI | `etl/load_vietjobs.py` dùng `HF_TOKEN`, chuẩn hoá lương và kinh nghiệm và bằng cấp, tách kỹ năng qua `skill_extractor` |
| ATS live Greenhouse và Lever và Ashby | `tasks.ingest_greenhouse_jobs` thân rỗng | VIẾT LẠI | Bỏ lốt Celery, chuyển thành `etl/ats_live.py` ghi thật xuống `job_posting` theo `job_key`, đọc token từ `data/sources.yaml` thay vì hard-code, kèm `reconcile` đổi trạng thái đóng tin sau 2 chu kỳ |
| Từ điển kỹ năng | `data/skill_alias.csv` 1.8 KB, khoảng 48 nhóm | MỞ RỘNG | Sinh `skill_taxonomy` từ tần suất kỹ năng trong 48k JD thật, giữ file CSV làm alias thủ công cho các biệt danh tiếng Việt; đây chính là chỗ bị bắt lỗi hôm trước khi CV dùng Airflow và Kafka và dbt |
| Skill graph PMI | Không có | MỚI | `etl/skill_graph.py` |
| CV parser: section, GPA, đồ án, liên hệ | Text và skills và kinh nghiệm và bằng cấp | MỞ RỘNG | Giữ `extract_text_from_pdf` và `docx` và `normalize_text` và `remove_diacritics`; thêm `split_sections`, `extract_gpa`, `extract_projects`, `extract_contacts`, trả về JSON schema bền hoá vào `cv_document.parsed_json` |
| Điểm sức khoẻ CV 6 tiêu chí | Không có | MỚI | `ml/cv_health.py` |
| MatchingScore 6 thành phần có học trọng số | 3 thành phần cố định | VIẾT LẠI trên nền cũ | Đổi skill overlap từ Jaccard union sang weighted coverage của JD, thêm semantic cosine và education và salary fit, đóng băng `model_version`, lưu `matching_result`, tinh chỉnh trọng số bằng grid search trên tập có nhãn |
| Embedding sentence-transformers | Không có | MỚI | `ml/build_embeddings.py` một phát batch 256, ghi `vector(384)` cho `job_posting` và `candidate` |
| Mô hình lương Random Forest | Không có, UI chỉ hiện `salary_min` và `max` | MỚI | `ml/salary_model.py` cộng baseline trung vị và `model_card.md`; Superset chỉ có AVG(salary_min) |
| AI viết lại outline CV | Không có | MỚI | `ml/outline_rewriter.py`, Gemini cộng fallback template cùng schema |
| API 7 endpoint | 3 endpoint thông minh, nhận profile từ query | MỞ RỘNG | `/cv/parse` nâng cấp và giữ; `/match/calculate` đổi thành `/match`; `/recommendations` bỏ query profile, đọc `candidate_id` từ token; thêm `/cv/{id}/health`, `/jobs/{id}/gap`, `/salary/estimate`, `/cv/outline` |
| Tính điểm trước cho toàn bộ tin mở | Không có | MỚI | Batch khi hồ sơ thay đổi để đáp ứng ngưỡng 5 giây |

### Checklist 3, BI

| Hạng mục plan | Code hiện có | Kết luận | Việc cụ thể |
|---|---|---|---|
| Helpers bootstrap | Toàn bộ | GIỮ | Không đụng |
| 3 dashboard phân vai | 1 dashboard "Job Portal BI" | MỞ RỘNG | Tách thành A thị trường lao động, B nhà tuyển dụng, C vận hành và chất lượng dữ liệu;dùng lại `ensure_dashboard` và `link_dashboard_charts` cho từng dashboard, thêm tham số tên và slug |
| 3 chỉ số đề bài: ứng viên theo kỹ năng | Chưa có chart nào về ứng viên (chart kỹ năng hiện tính trên `job_skills`, tức **cầu** chứ không phải **cung**) | MỚI | Chart mới trên `candidate_skill` |
| Xu hướng lương | 1 chart AVG(salary_min) theo địa điểm | MỞ RỘNG | Thêm p25 và trung vị và p75, thêm trục quý, thêm chênh lệch theo cấp bậc |
| Tỷ lệ chuyển đổi | Tỷ lệ trúng tuyển theo tuần | MỞ RỘNG | Thêm funnel screening và interview và offer, chia theo nguồn từ gợi ý hay tìm kiếm |
| 12 chỉ số đề xuất thêm | Không có | MỚI | Phân bố MatchingScore, đường hiệu chuẩn, CTR theo rank, chỉ số khan hiếm, kỹ năng trending, độ tươi dữ liệu, tỷ lệ tin công khai lương, cảnh báo đỏ `data_quality_metric` |
| `__timestamp` cho trend | Đã xử lý đúng | GIỮ | Bắt buộc giữ khi thêm chart mới |
| BI nhúng trong app | Không có trang `/bi` | MỚI | Iframe Superset cùng deep-link chart |

### Checklist 4, frontend

| Trang plan | Code hiện có | Kết luận |
|---|---|---|
| `login`, `register` | Có, chạy với backend | GIỮ, sửa `users` bảng thật và httpOnly cookie |
| `/student/profile` | `profile/page.tsx` lưu localStorage | VIẾT LẠI, gọi API và thêm kỹ năng cùng đồ án và GPA |
| `student/cv` tải CV | Không có trang, `api.uploadCV` trỏ endpoint ma | MỚI, nối `/api/v1/cv/parse` |
| `/jobs` và `/jobs/[id]` | Có UI, đọc mock trực tiếp và lưu saved vào localStorage | MỞ RỘNG, đổi sang API thật, badge điểm khớp thành phần |
| `/student/recommendations` | Tính client-side trên mock | VIẾT LẠI, gọi API, hiển thị lý do từng vị trí |
| `/student/cv-outline/[jobId]` | Không có | MỚI |
| `/student/applications` | Có UI, đọc localStorage | MỞ RỘNG sang API và funnel 5 bậc |
| `/employer/jobs`, `/employer/applicants`, `/employer/dashboard` | Không có | MỚI |
| `/bi` | Không có | MỚI |
| `/admin` | Có, đọc `/admin/stats` giả | MỞ RỘNG sang `ingestion_run` và `data_quality_metric` |
| Bỏ mock khỏi bundle | `mock/jobs.json` đang bị import trực tiếp vào client | BỎ vai trò nguồn dữ liệu, chuyển `tests/fixtures/jobs_10.json` |

### Checklist 5, kiểm thử và báo cáo

| Hạng mục plan | Code hiện có | Kết luận | Việc cụ thể |
|---|---|---|---|
| pytest đơn vị và tích hợp | Không có gì | MỚI | 10 file test cho parser và matching và ETL chuẩn hoá và API; fixture 10 job mock tái sử dụng làm dữ liệu test |
| Kiểm tra chất lượng dữ liệu | Không có | MỚI | `tests/test_data_quality.py` chạy SQL check, ghi `data_quality_metric` |
| E2E trình duyệt | Không có | MỚI | Agent chạy bằng browser-use, ảnh lưu `docs/qa/` |
| Đo p50 và p95 | Không có | MỚI | `scripts/loadtest.py` với httpx asyncio |
| `ml/evaluate.py` và metrics | Không có | MỚI | Chỉ số P@k và MRR và nDCG và MAE và MAPE và latency |
| Báo cáo đánh giá docx | Không có | MỚI | Script python-docx, giữ snapshot để hoàn tác |

---

## 4. Plan điều chỉnh thứ tự thi công khi kế thừa code cũ

Plan gốc có P0 dựng hạ tầng. Vì hạ tầng đã chạy nên P0 rút còn một nửa, và xuất hiện thêm một giai đoạn dọn dẹp mà plan gốc không có.

| Giai đoạn | Nội dung so với plan gốc | Khối lượng |
|---|---|---|
| P0' Dọn nền, **mới** | Thi công 6 quyết định ở Mục 5 (gỡ redis và worker và beat và celery_app và tasks, dựng Alembic cùng SQLAlchemy Core, JWT thật, fixture hoá mock) cộng sửa 4 lỗi ở Mục 2 (path traversal, `DELETE FROM job_skills`, backend đọc mock, hai công thức điểm lệch nhau) và khai ML libs vào `requirements.txt` | Ngắn, khoảng một buổi, toàn bộ agent làm |
| P1 | Checklist 1, giữ nguyên như plan | Trung bình |
| P2 | ETL, dồn vào ngay sau P1 vì không còn Celery stub để giữ chân | Trung bình tới dài, phụ thuộc `HF_TOKEN` |
| P3 | Checklist 2, `matching.py` và `cv_parser.py` mở rộng tại chỗ thay vì viết mới | Dài nhất |
| P4 | Checklist 3, cộng chart vào `bootstrap_superset.py`, ít rủi ro nhất vì pattern đã kiểm chứng | Trung bình |
| P5 | Checklist 4, chủ yếu là đổi nguồn dữ liệu của 8 trang và dựng 5 trang mới | Dài |
| P6 | Checklist 5 | Trung bình |

Rút kinh nghiệm từ plan gốc: P4 nay làm sớm hơn được một bậc vì Superset đã nối xong, chỉ cần schema mới là chart mới tự hiện. P5 vẫn phải chờ P3 vì UI cần điểm thật.

---

## 5. Sáu quyết định đã chốt ngày 2026-10-28 (ràng buộc thi công)

| # | Quyết định | Hệ quả trực tiếp lên code, agent làm |
|---|---|---|
| 1 | **Bỏ Celery và Redis.** Hạ tầng còn đúng 4 service chạy thường trực là postgres, backend, frontend, superset, cộng `superset-init` one-shot | Xoá `redis`, `worker`, `beat` khỏi `docker-compose.yml`; xoá `backend/app/celery_app.py` và `backend/app/tasks.py`; gỡ `celery==5.3.6` và `redis==5.0.1` khỏi requirements; 4 task chuyển thành package `etl/` và lịch `APScheduler` chạy trong backend; ingest 48k là script một phát `python -m etl.load_vietjobs`, có in tiến độ |
| 2 | **Giữ `seed_db.py` nhưng gắn cờ `SEED_MODE`** và in rõ ra log đang ở chế độ nào | `SEED_MODE=etl` (mặc định, đọc VietJobs và ATS xuống `job_posting`) hoặc `SEED_MODE=offline` (dùng fixture 10 tin cho demo khi HuggingFace không tải được). Backend in một dòng to ngay khi boot: "SEED MODE = offline (fixture 10 tin, DỮ LIỆU DEMO, không dùng cho số liệu BI)". Trang admin và dashboard BI hiển thị cờ này để không ai nhầm hai nguồn số liệu nữa |
| 3 | **SQLAlchemy Core cùng Alembic và thư mục SQL migration** | `backend/app/db.py` thay psycopg2 thủ công bằng engine SQLAlchemy giữ nguyên retry 30 lần lúc boot; `backend/db/migrations/` quản lý bằng Alembic, migration `0001_init` dựng 20 bảng và extension pgvector; `seed_db.py` chỉ còn nhiệm vụ seed, không tự `CREATE TABLE`; Superset đọc đúng schema đó nên chỉ còn một sự thật |
| 4 | **Weighted coverage của JD thay Jaccard union** | `matching.py:calculate_skill_overlap` viết lại: `sum(weight của kỹ năng JD được phủ) / sum(weight toàn bộ kỹ năng JD)`, có cộng một phần cho kỹ năng lân cận trên skill graph, không trừng phạt hồ sơ có kỹ năng thừa; UI sửa `recommendations/page.tsx:45` để dùng điểm do API trả, hai bên không còn hai công thức; **chạy lại đo số 0,87 và 0,26 trong deck rồi cập nhật, số mới sẽ cao hơn** |
| 5 | **JWT thật với bảng `users`** | `MOCK_USERS` và token `"mock-jwt-token-"` bị loại; mật khẩu băm bằng bcrypt hoặc argon2; đăng nhập cấp JWT ký bằng `JWT_SECRET`, hết hạn 7 ngày, lưu httpOnly cookie thay vì localStorage để khớp `NFR` bảo mật; `/users/me` đọc từ DB; `matching_result` và `application` có khoá ngoại tới ứng viên thật |
| 6 | **`mock/jobs.json` xuống fixture test, không xoá** | Đổi thành `tests/fixtures/jobs_10.json`; backend không còn đường đọc nào tới `frontend/mock` (bỏ khối tìm 4 lộ trình ở `main.py:16-23`); 8 trang frontend bỏ `import mockJobs`; fixture này nuôi test đơn vị parser và matching và chế độ `SEED_MODE=offline` của quyết định 2 |

---

## 6. Rủi ro của phương án kế thừa thay vì xây mới

| Rủi ro | Nguồn gốc | Cách phòng |
|---|---|---|
| Số liệu mới và cũ xung đột nhau trong slide bảo vệ | Slide và deck hiện tại đang trích 0,87 và 0,26 đo theo Jaccard 3 thành phần | Sau khi đổi công thức, chạy lại đúng hai hồ sơ đó và cập nhật số trong deck; không dùng song song |
| `superset-init` dựng chart trên schema cũ, thêm cột mới mà dataset không refresh | Đã gặp: dataset cache cột | Bootstrap phải gọi lại `ensure_dataset` và clear column cache mỗi lần schema đổi |
| Hot reload Next làm trang trắng vì chunk CSS cũ | Đã gặp ở phiên trước | Build tĩnh trước buổi demo và mở bằng `next start`, không dùng `next dev` khi trình bày |
| `requirements.txt` thêm torch transitively qua sentence-transformers, phình image | sentence-transformers kéo torch khoảng 2 GB | Khóa `torch` bản CPU-only index, hoặc cân nhắc TF-IDF cộng SVD thay embedding nếu image vượt 4 GB và máy thiếu RAM |
| Hai nguồn sự thật (RAM mock và Postgres) tái diễn | Đây là lỗi hệ thống của code cũ | Nguyên tắc cứng: backend không được đọc file JSON nào làm dữ liệu nghiệp vụ |
