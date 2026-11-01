# Plan triển khai: Nền tảng kết nối tuyển dụng thông minh (BI + AI)

Đề bài: AI tự động khớp kỹ năng ứng viên với yêu cầu công việc (Matching Score), tích hợp công cụ BI phân tích xu hướng thị trường lao động và báo cáo trực quan cho nhà tuyển dụng.

Tài liệu gốc làm nền: `Hệ Thống Tìm Việc Thông Minh BI và AI.pptx` (12 slide, đọc ngày 2026-10-28) gồm phương pháp luận ba trụ cột (ETL đa nguồn, khớp ngữ nghĩa, AI tạo sinh khuyến nghị), bảng 4 kênh dữ liệu ở slide 7, đặc tả thuật toán ở slide 9 (embeddings, Random Forest, gap analysis, RAG + LLM, OLAP cube) và bốn chỉ số đo lường ở slide 10 (85% độ chuẩn xác gợi ý, ±10% sai số lương, 3.2x tỷ lệ qua vòng lọc, dưới 5 giây phản hồi).

Ngày lập plan: 2026-10-28. Phạm vi: 5 checklist của đề bài, code cũ trong workspace tạm thời coi như chưa tồn tại, sau khi duyệt plan sẽ đối chiếu ở Mục 7.

---

## 0. Các quyết định đã chốt và ràng buộc

| Hạng mục | Quyết định | Lý do |
|---|---|
| Stack | PostgreSQL 16 + pgvector, FastAPI, Next.js, Apache Superset 6.1, scikit-learn + sentence-transformers chạy CPU | Miễn phí, số dịch vụ runtime đúng 4, không Kafka/Elasticsearch/Milvus/MinIO |
| Lịch chạy nền | Bỏ Celery + Redis, dùng APScheduler trong backend và script one-shot cho việc nặng. Hạ tầng còn 4 service chạy thường trực | Giảm 2 dịch vụ và giảm rủi ro demo (chốt 2026-10-28) |
| Tầng dữ liệu | SQLAlchemy Core cộng Alembic và thư mục SQL migration, bỏ psycopg2 thủ công; schema là sự thật duy nhất vì Superset đọc cùng DB | Chốt 2026-10-28, hết cảnh backend đọc RAM còn Postgres đọc seed |
| Auth | JWT thật ký bằng `JWT_SECRET`, mật khẩu băm bcrypt, bảng `users`, cookie httpOnly | Chốt 2026-10-28; `matching_result` và `application` cần khoá ngoại tới ứng viên thật |
| Công thức khớp kỹ năng | Weighted coverage của JD, không dùng Jaccard union | Chốt 2026-10-28; Jaccard union phạt hồ sơ có nhiều kỹ năng và làm hai phía backend và UI cho hai điểm khác nhau |
| Chế độ dữ liệu | Cờ `SEED_MODE=etl` mặc định, `SEED_MODE=offline` cho demo, backend in rõ chế độ đang chạy lên log và trang admin | Chốt 2026-10-28; phòng lỗi hai nguồn số liệu song song |
| Fixture test | 10 tin `frontend/mock/jobs.json` chuyển thành `tests/fixtures/jobs_10.json`, backend và UI không còn đường đọc mock | Chốt 2026-10-28, không xoá file |
| Kênh 1 dữ liệu | VietJobs 48.092 tin (HuggingFace, cần token) cho kho phân tích và lương, cộng ATS công khai Greenhouse/Lever/Ashby cho tin đang mở | Đã kiểm chứng repo có sẵn cột `technical_skills`, `soft_skills`, `salary_min/max/avg`, `category`, `location`, `qualifications`, `experience_required`; giấy phép CC BY 4.0; board `navervietnam` trả về HTTP 200 với 7 tin thật |
| Kênh 2 dữ liệu | Skill graph tự xây từ đồng xuất hiện kỹ năng trong JD thật (PMI) thay cho LinkedIn API | LinkedIn và Indeed Publisher đã đóng, không xin được key |
| Kênh 3 dữ liệu | Dải lương p25/trung vị/p75 suy từ `salary_min/max/avg` tự khai, gắn nhãn nguồn rõ là "từ tin đăng", có Random Forest định giá | Báo cáo lương thường niên (Navigos, ManpowerGroup) là PDF có bản quyền |
| Kênh 4 dữ liệu | Kho hồ sơ chuẩn lấy từ pattern JD thành công + 1 tới 2 CV thật do bạn cung cấp (tuỳ chọn) | Không có kho CV cựu sinh viên |
| AI tạo sinh | Gemini free-tier key cho phần viết lại outline CV và giải thích khớp, có fallback deterministic cục bộ cùng schema JSON | Free tier đổi giới hạn liên tục (có giai đoạn Flash bị ghi nhận chỉ 20 request/ngày), demo không được phép chết vì quota |
| Mô nhúng | `paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều, CPU, tính một lần rồi lưu vào pgvector | Nhẹ, đa ngôn ngữ phù hợp JD tiếng Việt, không cần GPU (máy không có nvidia-smi) |
| Máy chủ demo | 15,3 GB RAM, D: còn 240 GB, Docker Desktop đã cài nhưng daemon đang tắt | Vừa đủ cho Superset + Postgres + backend |

Bốn ràng buộc chất lượng trích thẳng từ slide 10 mà plan này phải đo được: độ chuẩn xác gợi ý, sai số dự báo lương, tỷ lệ qua vòng lọc, thời gian phản hồi. Mọi con số đưa ra trong báo cáo và slide là số đo thật; cái nào không đo được thì ghi là không đo được, không bịa.

---

## 1. CHECKLIST 1 — Phân tích yêu cầu hệ thống và thiết kế CSDL

### 1.1 Phân tích yêu cầu (agent viết, bạn chỉ duyệt)

- Tài liệu `docs/01-yeu-cau-va-thiet-ke.md`: bối cảnh, ba nhóm vai trò (sinh viên/ứng viên, nhà tuyển dụng, quản trị), biểu đồ use case dạng Mermaid.
- Danh sách yêu cầu chức năng đánh số `FR-01` tới `FR-30` và phi chức năng `NFR-01` tới `NFR-12` (bảo mật JWT + RBAC, hiệu năng dưới 5 giây, khả năng mở rộng, độ trễ dữ liệu, miễn phí 100%, chạy offline được phần cốt lõi).
- Bảng truy vết (traceability matrix): mỗi dòng là một yêu cầu của đề bài hoặc một nội dung trong 12 slide, cột bên phải trỏ tới API, bảng CSDL, trang UI và test case tương ứng. Bảng này là căn cứ để giảng viên thấy không có mục nào của đề bài bị bỏ.
- Phát hiện sớm hai điểm không thể đáp ứng như thiết kế gốc và ghi rõ cách thay thế: LinkedIn API (thay bằng skill graph) và báo cáo lương PDF (thay bằng dải lương từ tin đăng).

### 1.2 Thiết kế CSDL

Sơ đồ ERD Mermaid trong `docs/02-erd.md`, DDL trong `backend/db/migrations/001_init.sql`, chạy tự động khi container Postgres khởi tạo lần đầu.

Nhóm bảng chính:

| Bảng | Nội dung chính | Ghi chú thiết kế |
|---|---|---|
| `skill_taxonomy` | tên kỹ năng, biệt danh (aliases), nhóm ngành, loại technical/soft/language | Xây từ tần suất xuất hiện trong 48k JD, chuẩn hoá bằng alias, kỳ vọng 300 tới 600 kỹ năng |
| `occupation_graph` | cặp kỹ năng hoặc kỹ năng tới chức danh, trọng số PMI | Kênh 2, dùng cho gợi ý theo ngành và gap analysis có suy rộng |
| `company` | tên, ATS board, quy mô, địa điểm, ngành | Nhà tuyển dụng |
| `job_posting` | job_key, title, category, location, remote, contract, kinh nghiệm, trình độ, `salary_min/avg/max`, currency, `salary_source`, mô tả, yêu cầu, phúc lợi, `source` (vietjobs / greenhouse / lever / ashby / synthetic), `status` (open / closed), `posted_at`, `first_seen_at`, `last_seen_at`, embedding `vector(384)` | Cơ chế đóng tin: job_key không xuất hiện 2 chu kỳ quét liên tiếp thì chuyển status sang closed |
| `job_skill` | job_id, skill_id, `required`, trọng số, số lần nhắc | Nền của tính điểm khớp |
| `candidate` | hồ sơ số: chuyên ngành, GPA, năm tốt nghiệp, định hướng, kinh nghiệm, mong muốn lương/địa điểm, embedding `vector(384)` | Ứng viên |
| `cv_document` | file, text thô, trạng thái parse, `cv_health_score`, parsed JSON | Phân tích cục bộ hồ sơ (slide 6) |
| `candidate_skill` | skill_id, số năm, nguồn bằng chứng (CV, tự khai, đồ án), độ tin cậy | |
| `academic_project` | tên đồ án, công nghệ, kết quả định lượng, `depth_score` | Qui đổi bài tập lớn thành kinh nghiệm thực chiến (slide 6) |
| `application` | candidate_id, job_id, trạng thái funnel (created, screening, interview, offer, rejected), mốc đổi trạng thái, nguồn (tìm kiếm hay gợi ý) | Dùng cho tỷ lệ chuyển đổi và time-to-fill |
| `matching_result` | điểm tổng và điểm từng thành phần, danh sách kỹ năng khớp/thiếu, `explanation_json`, `model_version` | Lưu để BI vẽ phân bố điểm và để tái lập giải thích |
| `cv_outline_suggestion` | outline JSON, model đã dùng, thời điểm sinh | Tính năng đột phá slide 8 |
| `recommendation_event` | candidate, job, vị trí xếp hạng, đã xem, đã bấm, đã ứng tuyển | Đo CTR theo rank, chứng minh gợi ý hiệu quả |
| `ingestion_run` | nguồn, thời lượng, số bản ghi vào/upsert/mới/đóng, lỗi | Vận hành ETL |
| `data_quality_metric` | run_id, chiều đo (completeness, uniqueness, validity, consistency, timeliness, accuracy), bảng, cột, giá trị, ngưỡng, trạng thái | Phục vụ dashboard chất lượng dữ liệu |
| `audit_log` | ai làm gì khi nào | Cho vai trò quản trị |

Tầng BI: view theo mô hình sao gồm `fact_application`, `fact_matching`, `fact_job_posting`, `dim_skill`, `dim_location`, `dim_time`, cùng view `v_salary_band` (dải lương theo ngành, địa điểm, kinh nghiệm) và `v_skill_supply_demand`. Các view nặng sẽ chuyển thành materialized view có lệnh refresh trong chu kỳ ETL.

Index: HNSW trên hai cột embedding, GIN trên cột tsvector cho toàn văn tiếng Việt có dấu (đặt `to_tsvector('simple', ...)` để không phụ thuộc dictionary tiếng Việt), B-tree trên `status`, `location`, `category`, unique trên `job_key`.

Ràng buộc toàn vẹn và dữ liệu tham chiếu: seed danh mục kỹ năng, địa điểm 63 tỉnh, ngành nghề, ba tài khoản demo (một sinh viên, một nhà tuyển dụng, một admin) với mật khẩu ghi trong `docs/accounts.md`.

### 1.3 Điều kiện hoàn thành checklist 1

`docker compose up` chạy sạch, migration áp dụng không lỗi, ERD và tài liệu yêu cầu nằm trong `docs/`, 48k tin đã vào bảng `job_posting`, báo cáo chất lượng dữ liệu đầu tiên được sinh tự động.

---

## 2. CHECKLIST 2 — Mô hình AI/ML phân tích CV và tính Matching Score

### 2.1 Pipeline ETL và tách kỹ năng (nền của mọi mô hình)

- `etl/load_vietjobs.py`: tải parquet/CSV từ HuggingFace bằng token, chuẩn hoá tiếng Việt, tách `salary` dạng "15.0 - 22.0 triệu" về VND/tháng, suy ra `experience_years` từ chuỗi "1 năm", "Không yêu cầu", tách bằng cấp từ `qualifications`.
- `etl/skill_extractor.py`: khớp từ điển alias, xấp xỉ chuỗi bằng `rapidfuzz` cho biến thể (PostgreSQL, Postgre SQL, postgres), giới hạn tỉ lệ sai số, thống kê những JD không trích được kỹ năng nào để bổ sung từ điển.
- `etl/skill_graph.py`: xây `occupation_graph` bằng PMI trên đồng xuất hiện kỹ năng trong cùng tin đăng, cắt cạnh yếu.
- `etl/ats_live.py`: quét Greenhouse, Lever, Ashby theo danh sách token cấu hình trong `data/sources.yaml`, upsert theo `job_key`, đánh dấu tin đóng, lấy cả URL gốc để chứng minh nguồn khi bảo vệ.
- `ml/build_embeddings.py`: script one-shot batch 256, chạy lúc khởi tạo và khi có tin mới, tiến độ in ra log.

### 2.2 Phân tích CV (slide 6 và slide 2: bóc tách thực thể, độ sâu đồ án, sức khoẻ CV)

- `ml/cv_parser.py`: pypdf và pdfplumber đọc text, chia section bằng regex tiêu đề Việt và Anh, nhận diện thực thể bằng từ điển kỹ năng cộng mẫu hình (email, SĐT, GPA, số năm kinh nghiệm, tên trường, chứng chỉ), xuất JSON đúng schema `cv_document.parsed_json`.
- `ml/cv_health.py`: rubric 6 tiêu chí có trọng số, mỗi tiêu chí trả về vấn đề cụ thể (thiếu mục kỹ năng, không có số liệu định lượng trong kết quả, CV dài quá, thiếu email, kỹ năng ít hơn ngưỡng ngành, mô tả chung chung kiểu "môi trường năng động" như slide 8 nêu).
- `ml/project_depth.py`: chấm độ sâu đồ án theo số công nghệ, có kết quả định lượng, có vai trò cá nhân.

### 2.3 Matching Score có giải thích (trọng tâm đề bài)

Điểm tổng là tổ chức có trọng số của sáu thành phần, tất cả lưu vào `matching_result` để tái lập:

| Thành phần | Cách tính | Trọng số khởi điểm |
|---|---|---|
| Kỹ năng | Tỷ lệ kỹ năng có trọng số của JD được phủ, có cộng một phần cho kỹ năng lân cận trên skill graph; thay Jaccard union đang dùng ở `matching.py:22` vì công thức cũ phạt hồ sơ có nhiều kỹ năng | 0.35 |
| Ngữ nghĩa | cosine giữa embedding bản tóm tắt hồ sơ và embedding JD | 0.25 |
| Kinh nghiệm | hàm bậc thang theo số năm JD yêu cầu, dương cho ứng viên vượt, không phạt quá nặng | 0.15 |
| Trình độ | khớp bằng cấp theo `qualifications` | 0.08 |
| Địa điểm | cùng tỉnh, hoặc remote, hoặc lân cận | 0.10 |
| Lương | mức mong muốn nằm trong bao nhiêu phần dải lương của tin | 0.07 |

- Trọng số không đặt tuỳ hứng: khởi tạo bằng grid search trên tập đánh giá có nhãn (Mục 2.6), sau đó đóng băng thành `model_version` ví dụ `match-v1.3` để mọi con số trong báo cáo gọi được về đúng phiên bản.
- `ml/gap_analysis.py`: danh sách kỹ năng thiếu sắp theo độ khan hiếm của ngành (kỹ năng thiếu xuất hiện trong bao nhiêu phần trăm tin cùng category), kèm đường học bổ sung từ skill graph.
- `ml/explain.py`: sinh văn bản giải thích từ chính các thành phần, ví dụ "khớp 7/10 kỹ năng, thiếu FastAPI và Redis là hai kỹ năng có trong 68% tin Backend cùng cấp", không để mô hình hộp đen.
- Ngưỡng hiển thị: từ 0.75 rất phù hợp, 0.55 tới 0.75 khá, dưới 0.55 thấp.
- API: `POST /api/v1/cv/parse`, `GET /api/v1/cv/{id}/health`, `POST /api/v1/match`, `GET /api/v1/recommendations?k=20`, `GET /api/v1/jobs/{id}/gap`, `GET /api/v1/salary/estimate`, `POST /api/v1/cv/outline`.
- Tối ưu tốc độ: điểm khớp của hồ sơ với các tin đang mở tính sẵn theo lô khi hồ sơ thay đổi, trang gợi ý chỉ đọc bảng `matching_result`, bảo đảm yêu cầu dưới 5 giây kể cả khi kho vài nghìn tin.

### 2.4 Mô hình định giá lương (slide 9 Random Forest, slide 10 ±10%)

- `ml/salary_model.py`: features gồm one-hot `category` và `location`, số năm kinh nghiệm, bằng cấp, số kỹ năng, cờ Fresher/Intern/Junior, loại hợp đồng; target là `log(salary_avg)`. So sánh ba mô hình: baseline trung vị theo phân khúc, GradientBoosting, RandomForest; chọn mô hình thắng trên test split, giữ baseline làm chuẩn đối chiếu.
- Split theo hash `job_key` để không rò rỉ tin trùng.
- Output API trả cả hai: dải thực chứng p25/trung vị/p75 (dùng làm câu trả lời chính cho sinh viên, an toàn khi mô hình sai) và điểm ước lượng của mô hình kèm khoảng tin cậy.
- `models/model_card.md`: dữ liệu huấn luyện, đặc trưng, chỉ số, giới hạn (lương tự khai nên bị thiên vị, không phải lương thực nhận).

### 2.5 AI viết lại outline CV (slide 8, RAG và LLM)

- `ml/outline_rewriter.py`: bước retrieve lấy JD top khớp, kỹ năng thiếu, ba pattern mở đầu và mô tả kết quả tốt nhất học từ `v_skill_supply_demand` cùng rubric; bước generate gọi Gemini với prompt ép trả về JSON đúng schema; fallback cục bộ dùng template cùng schema khi hết quota hoặc mất mạng.
- Output là dàn ý mới: tóm tắt định lượng nêu vị trí và ba kỹ năng lõi khớp JD, đẩy đồ án lên trên theo công thức Bài toán, Giải pháp, Kết quả, chèn từ khóa còn thiếu, trọng tâm đổi theo từng công ty, kèm bảng so sánh trước và sau để UI hiển thị diff.
- Cache theo bộ ba (candidate, job, model_version) để mỗi lần bấm nút chỉ tốn một request.

### 2.6 Tập đánh giá có nhãn (điểm cần bạn duyệt)

Checklist 5 yêu cầu đo hiệu quả mô hình gợi ý nên bắt buộc phải có nhãn. Vì kho CV cựu sinh viên không tồn tại, plan đề xuất **weak supervision tự động từ dữ liệu thật**: chọn một tin đăng làm mục tiêu, sinh hồ sơ dương bằng cách lấy chính kỹ năng, kinh nghiệm, bằng cấp của tin đó; sinh hồ sơ phủ định khó bằng cách lấy profile của tin cùng ngành nhưng khác tập kỹ năng hoặc khác cấp bậc. Nhãn là nhãn suy diễn, ghi rõ phương pháp trong báo cáo. Chỉ số đo được: Precision@1/3/5/10, Recall@k, MRR, nDCG@10, độ hiệu chuẩn (tỷ lệ pass thật theo khoảng điểm), độ nhạy với nhiễu (thêm/bớt kỹ năng thì điểm đổi bao nhiêu).

Nếu bạn không đồng ý với nhãn suy diễn, thay bằng phương án chuyên gia: bạn hoặc giảng viên chấm tay 20 cặp CV và JD ở ba mức, chỉ số chuyển thành đồng thuận Spearman và top-accuracy trên 20 cặp. Plan đang viết theo phương án suy diễn; nói một tiếng nếu bạn muốn đổi.

### 2.7 Điều kiện hoàn thành checklist 2

Chạy `python -m ml.evaluate` sinh ra `reports/metrics.json` và `reports/model_card.md`; Swagger gọi được cả bảy endpoint; điểm khớp của một cặp cố định tái lập đúng khi chạy lại (kiểm định tính tất định); CV mẫu parse ra đủ kỹ năng và số năm kinh nghiệm; thời gian phản hồi đo được dưới 5 giây.

---

## 3. CHECKLIST 3 — Dashboard BI và hệ chỉ số

### 3.1 Ba dashboard trong Superset

`superset/bootstrap_superset.py` chạy one-shot, tự tạo kết nối Postgres, dataset, chart và dashboard, tự liên kết bảng `dashboard_slices` bằng INSERT. Script dùng đúng các kiêng kỵ đã rút ra từ phiên trước: ảnh Superset phải cài `psycopg2-binary` bằng `uv pip install --python /app/.venv/bin/python`; chart tạo qua REST phải có cả `params` lẫn `query_context`; pie dùng khoá `echarts_pie` sẽ lỗi, phải dùng `pie` với `formData.metric` số ít; trend phải có `__timestamp` trong `columns` mới lên trục thời gian; viz `table` bắt buộc có `table_timestamp`.

| Dashboard | Đối tượng | Nội dung |
|---|---|---|
| A. Thị trường lao động cho sinh viên | Công khai | ba chỉ số đề bài yêu cầu cộng các chỉ số đề xuất |
| B. Nhà tuyển dụng | Employer | chất lượng nguồn ứng viên và funnel |
| C. Vận hành và chất lượng dữ liệu | Admin, giảng viên | ETL runs, độ tươi, lỗi chất lượng |

### 3.2 Hệ chỉ số

Ba chỉ số đề bài yêu cầu, triển khai ưu tiên:

1. Số lượng ứng viên theo kỹ năng: `candidate_skill` group by skill, sắp top 20, có bộ lọc địa điểm và ngành.
2. Xu hướng lương: `v_salary_band` vẽ p25, trung vị, p75 theo ngành và địa điểm, thêm trục thời gian theo quý của `posted_at` để thấy dịch chuyển.
3. Tỷ lệ chuyển đổi tuyển dụng: funnel từ `application`, tính screening tới interview, interview tới offer, tỷ lệ trúng tuyển chung (số offer trên số hồ sơ) và tỷ lệ theo nguồn (từ gợi ý so với từ tìm kiếm).

Chỉ số đề xuất thêm, nhóm theo mục đích, đều tính được từ schema Mục 1:

- Nhóm cung cầu: tỷ lệ cung trên cầu theo kỹ năng (chỉ số khan hiếm), số tin mở theo ngành và địa điểm, tốc độ tăng tin đăng theo tuần, kỹ năng trending và kỹ năng suy giảm theo tuần.
- Nhóm giá trị thị trường: chênh lệch lương theo kỹ năng (kỹ năng nào đội giá lên bao nhiêu phần trăm so với trung vị ngành), khoảng lương theo cấp bậc, tỷ lệ tin công khai lương (chỉ số minh bạch dữ liệu).
- Nhóm hiệu quả mô hình: phân bố MatchingScore, đường hiệu chuẩn giữa điểm và tỷ lệ vào vòng sau, CTR theo vị trí xếp hạng top-1 tới top-20, tỷ lệ ứng tuyển khi điểm vượt ngưỡng 0.75 so với dưới 0.55 (chỉ số 3.2x của slide 10 sẽ được thay bằng số đo thật ở đây), số kỹ năng thiếu trung bình của hồ sơ bị loại.
- Nhóm vận hành: thời gian từ ứng tuyển tới phản hồi, thời gian lấp chỗ trống, số tin đóng mỗi chu kỳ, độ trễ dữ liệu, tỷ lệ trùng và tỷ lệ thiếu trường từ `data_quality_metric`.

### 3.3 BI nhúng trong ứng dụng

Trang `/employer/dashboard` và `/bi` trong Next.js: năm KPI tự vẽ bằng recharts để employer không cần rời hệ thống, phần phân tích sâu nhúng iframe Superset kèm deep-link tới từng chart. Quyền truy cập theo vai trò, Superset chạy chế độ light-only, không cho sửa chart từ UI demo.

### 3.4 Điều kiện hoàn thành checklist 3

Script bootstrap in ra bảng xác nhận: mỗi chart gọi `POST /api/v1/chart/data` trả về ít nhất một hàng thật. Toàn bộ chart JSON được xuất về `superset/exported/` để lần chạy sau dựng lại y hệt. Ảnh chụp màn hình từng dashboard lưu ở `docs/qa/`.

---

## 4. CHECKLIST 4 — Frontend và tích hợp API AI/BI

### 4.1 Tuyến trang

| Route | Vai trò | Nội dung và API gọi |
|---|---|---|
| `/login`, `/register` | Mọi vai trò | JWT httpOnly cookie |
| `/student/dashboard` | Ứng viên | tóm tắt hồ sơ, điểm sức khoẻ CV, số việc khớp |
| `/student/profile` | Ứng viên | kỹ năng, GPA, đồ án, mong muốn lương, `/api/v1/candidate` |
| `/student/cv` | Ứng viên | nút tải CV lên, gọi `POST /api/v1/cv/parse`, hiển thị kỹ năng trích được và rubric |
| `/jobs` | Ứng viên | tìm kiếm, bộ lọc, badge MatchingScore trên mỗi card |
| `/jobs/[id]` | Ứng viên | giải thích điểm theo thành phần, gap analysis, nút ứng tuyển và lưu |
| `/student/recommendations` | Ứng viên | Top-K cá nhân hoá đọc từ `matching_result`, kèm lý do từng vị trí, không tính lại client-side |
| `/student/cv-outline/[jobId]` | Ứng viên | diff outline cũ và outline AI, bản fallback khi Gemini hết quota |
| `/student/applications` | Ứng viên | bảng trạng thái funnel, mốc thời gian |
| `/employer/jobs` | Nhà tuyển dụng | tạo và quản lý tin, import từ ATS |
| `/employer/applicants` | Nhà tuyển dụng | danh sách ứng viên sắp theo điểm, bộ lọc kỹ năng thiếu |
| `/employer/dashboard` | Nhà tuyển dụng | KPI nhóm cung cầu và funnel |
| `/bi` | Mọi vai trò theo quyền | iframe Superset |
| `/admin` | Quản trị | ETL runs, data quality, danh sách kỹ năng, tài khoản |

### 4.2 Yêu cầu tích hợp

Client API có kiểu tường minh (`frontend/lib/api.ts`), một biến môi trường `NEXT_PUBLIC_API_BASE`, không còn mock dataset trong luồng chính (đây là điểm bị bắt lỗi ở buổi demo trước: trang gợi ý tính điểm client-side trên mock và không có nút tải CV), trạng thái loading, lỗi, rỗng cho mọi khối dữ liệu, hiển thị nguồn và timestamp của từng con số để chống nghi vấn "số này ở đâu ra" khi bảo vệ.

### 4.3 Điều kiện hoàn thành checklist 4

Agent tự mở trình duyệt, chạy hết luồng vàng: đăng nhập, tải CV, parse, xem gợi ý, bấm vào một tin có giải thích khớp, ứng tuyển, xem dashboard employer, mở Superset; đồng thời chạy các luồng biên (CV không parse được, tài khoản chưa có hồ sơ, quota Gemini hết, không có tin nào khớp). Ảnh chụp từng bước lưu ở `docs/qa/`.

---

## 5. CHECKLIST 5 — Kiểm thử và báo cáo đánh giá

### 5.1 Bốn tầng kiểm thử (agent viết và chạy toàn bộ)

1. Đơn vị với pytest: parser, chuẩn hoá lương, tách kỹ năng, sáu hàm tính điểm, rubric CV health, hàm sinh outline. Mục tiêu phủ 80% module `ml/` và `etl/`.
2. Tích hợp: FastAPI test client trên Postgres thật, dựng schema bằng fixture, kiểm tra phân quyền và tính tất định của `matching_result`.
3. Chất lượng dữ liệu: bộ kiểm tra SQL cho sáu chiều (thiếu trường, trùng `job_key`, lương âm hoặc quá trần, kỹ năng mồ côi, tin đóng mà còn mở quá 30 ngày, độ tươi nguồn), kết quả ghi vào `data_quality_metric` và hiển thị cảnh báo đỏ ở dashboard C.
4. End-to-end và hiệu năng: luồng trình duyệt như Mục 4.3, cộng script áp lực song song đo p50 và p95 của `POST /api/v1/match` và `GET /api/v1/recommendations` để đối chiếu con số dưới 5 giây của slide 10.

### 5.2 Đánh giá mô hình

`ml/evaluate.py` xuất `reports/metrics.json` gồm Precision@k, Recall@k, MRR, nDCG@10, độ hiệu chuẩn, MAE và RMSE và MAPE của mô hình lương so với baseline trung vị, độ nhạy điểm theo nhiễu kỹ năng, thời gian phản hồi. Mỗi run kèm hash của model, dữ liệu và seed để tái lập.

### 5.3 Báo cáo

`docs/bao-cao-danh-gia.md` và bản `.docx` sinh bằng script python-docx (giữ script để hoàn tác một lệnh nếu bạn muốn bản trước), bố cục: yêu cầu và thiết kế, phương pháp mô hình, bộ dữ liệu và cách lấy nhãn, kết quả đo thật theo bảng, so sánh với bốn mục tiêu của slide 10, phân tích sai số kèm ví dụ thất bại điển hình, hạn chế, hướng cải tiến. Mục hạn chế bắt buộc có: dữ liệu là snapshot nên tin đã đóng, lương do tin đăng tự khai không phải thực nhận, chưa có người dùng thật nên chỉ đánh giá offline, Gemini bị giới hạn quota.

### 5.4 Điều kiện hoàn thành checklist 5

Toàn bộ pytest xanh, số liệu trong báo cáo khớp từng chữ số với `metrics.json`, tài liệu đọc được độc lập không cần giải thích miệng.

---

## 6. Lộ trình, thứ tự chạy và tỷ lệ tự động

| Giai đoạn | Việc | Agent làm | Bạn làm | Mốc thời gian gợi ý |
|---|---|---|---|---|
| P0 Dọn nền | Thi công 6 quyết định kế thừa code (xem Mục 5 file delta): gỡ redis và worker và beat và celery_app và tasks, dựng Alembic cùng SQLAlchemy Core, JWT thật, fixture hoá mock, sửa 4 lỗi hệ thống, khai ML libs, kiểm tra daemon Docker | 100% | Bật Docker Desktop (tôi có thể lệnh mở, nhưng cần bạn bấm nếu phải đăng nhập GUI) | 1 buổi |
| P1 Checklist 1 | tài liệu yêu cầu, truy vết, ERD, DDL, migration | 100% | Duyệt bảng FR và ERD một lượt | 1 tới 2 buổi |
| P2 ETL và skill graph | tải VietJobs, chuẩn hoá, tách kỹ năng, quét ATS | 100% | Cấp token HuggingFace và dán `HF_TOKEN` vào `.env` (khoảng 5 phút, làm một lần) | 1 tới 2 buổi |
| P3 Checklist 2 | CV parser, MatchingScore, mô hình lương, outline AI, evaluate | 100% | Dán `GEMINI_API_KEY` vào `.env`; duyệt phương án nhãn ở Mục 2.6; nếu chọn phương án chuyên gia thì chấm 20 cặp (15 phút) | 3 tới 5 buổi |
| P4 Checklist 3 | bootstrap Superset, ba dashboard, KPI nhúng | 100% | Ngắm dashboard và sắp xếp thứ tự chart nếu muốn | 2 buổi |
| P5 Checklist 4 | UI các route, tích hợp API, test bằng trình duyệt | 100% | Xem demo thử và chốt luồng nào cần đổi | 3 tới 4 buổi |
| P6 Checklist 5 | pytest, kiểm tra chất lượng dữ liệu, áp lực, báo cáo docx | 100% | Đọc báo cáo một lượt | 1 tới 2 buổi |

Tổng số việc manual dự kiến của bạn: bốn hành động (bật Docker, dán hai key vào `.env`, duyệt ba quyết định phương pháp, optional upload CV và chấm 20 cặp). Không có bước nào phải viết code.

Thứ tự P2 tới P3 là chuỗi tới hạn vì mô hình cần dữ liệu. P4 chỉ phụ thuộc P1 và P2, có thể làm sớm hơn nếu bạn muốn có hình để trình. P5 nên chờ P3 xong ít nhất phần matching để UI hiển thị số thật thay vì mock.

---

## 7. Bước đối chiếu code cũ (ĐÃ HOÀN THÀNH ngày 2026-10-28)

Kết quả kiểm kê 40 file nguồn nằm ở `PLAN-DELTA-VOI-CODE-CU.md`: tỷ lệ reuse theo từng khu (hạ tầng và Superset khoảng 75%, parser 35%, matching 30%, ETL 10%, schema 20%, frontend 40%, BI 50%, ML lương và embedding và test và báo cáo 0%), bảng verdict GIỮ và MỞ RỘNG và VIẾT LẠI và BỎ cho từng hạng mục của 5 checklist, bốn lỗi hệ thống phải sửa, và sáu quyết định kế thừa đã được bạn chốt (Mục 5 file delta). Những con số ví dụ nêu trong bản nháp trước như `matching.py` Jaccard, `seed_db.py` 120 hồ sơ, `bootstrap_superset.py` 13 chart, `tasks.py` stub, `/recommendations` tính client-side nay đều đã được kiểm chứng và dẫn line cụ thể trong file delta.

Tổng khối lượng còn lại ước khoảng 65% plan, đổi lại P0 dựng hạ tầng rút còn một buổi dọn nền vì compose, Superset bootstrap và pattern seed idempotent đã chạy thật.

---

## 8. Rủi ro đã lường và cách xử lý

| Rủi ro | Xử lý trong plan |
|---|---|
| HuggingFace từ chối quyền truy cập dataset hoặc file quá nặng | Project vào `data/VietJobs_sample.csv` chính thức trên GitHub làm nguồn khởi động, pipeline không đổi, chỉ giảm volume; luôn giữ ATS live |
| Gemini free tier hết quota giữa buổi bảo vệ | Fallback template deterministic cùng schema, có cờ hiển thị "đang dùng chế độ offline", không lỗi màn hình |
| Superset dựng chart im lặng trả về rỗng | Script bootstrap assert mỗi chart phải trả ít nhất một hàng qua `/api/v1/chart/data`, không đạt thì fail loudly |
| Embedding 48k tin trên CPU chậm | Script one-shot chạy nền một lần, cache pgvector, UI chỉ đọc kết quả |
| Machine không còn đủ RAM vì Superset và Postgres | Bật cấu hình memory limit cho từng service trong compose, Superset chỉ chạy khi demo BI |
| Dữ liệu lương thiên vị và MAPE vượt xa ±10% của slide 10 | Trả dải p25 tới p75 làm câu trả lời chính, ghi số đo thật trong báo cáo thay vì cam kết ±10% |
| CSS bundle cũ gây trắng trang khi hot-reload (đã gặp) | Build tĩnh trước demo, kiểm tra bằng trình duyệt ở P5, không phụ thuộc dev server |

---

## 9. Việc cần bạn làm để bắt đầu

Sáu quyết định kế thừa code đã chốt ngày 2026-10-28 và đã đưa vào Mục 0 ở trên cùng Mục 5 của file delta, không còn question mở nào về kiến trúc.

Chỉ còn ba việc, và **không việc nào chặn P0**:

1. Bật Docker Desktop. Đây là việc duy nhất cần làm trước, vì P0 dọn nền chỉ sửa compose, requirements, auth và migration.
2. Cấp `HF_TOKEN` cho VietJobs trước P2, `GEMINI_API_KEY` trước P3; bạn tự dán vào `.env` để key không đi qua hội thoại.
3. Duyệt phương án nhãn ở Mục 2.6 (weak supervision suy từ JD thật, hay chuyên gia chấm 20 cặp). Việc này chặn P3 phần đánh giá chứ không chặn code.
