# Job Suggestion: nền tảng kết nối tuyển dụng thông minh (BI + AI)

Khớp kỹ năng CV với tin tuyển dụng (Matching Score có giải thích), phân tích CV, gợi ý sửa CV (Gemini, có fallback offline),
và dashboard BI cho thị trường lao động và nhà tuyển dụng.

## Chạy nhanh

> 📖 **Xem hướng dẫn chi tiết:** Xem file **[HDSD.md](HDSD.md)** để biết chi tiết từng bước khởi chạy bằng Docker, danh sách tài khoản demo và kịch bản nghiệm thu tính năng.

Yêu cầu: Docker Desktop. Tùy chọn: dán `GEMINI_API_KEY` vào `.env` (không có key vẫn chạy đủ, gợi ý sửa CV dùng mẫu offline).

```bash
docker compose up -d --build
```

Lần đầu backend tự áp schema, tải VietJobs từ HuggingFace (mẫu ~3500 tin), sinh ứng viên mô phỏng và huấn luyện mô hình (vài phút).

| Dịch vụ | URL |
|---|---|
| Web | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| Superset (admin/admin) | http://localhost:8088 — dashboard `thi-truong-lao-dong` và `tuyen-dung` |

Tài khoản demo: xem [ACCOUNTS.md](ACCOUNTS.md) (mật khẩu `demo123`).

## Kiến trúc

`postgres` (nguồn dữ liệu duy nhất) · `backend` FastAPI + scikit-learn · `frontend` Next.js · `superset` + `superset-init`.
Không dùng GPU, embedding hay Celery/Redis.

## Phát triển và kiểm thử (ngoài Docker)

```bash
docker compose up -d postgres
cd backend && pip install -r requirements.txt
python -m app.seed_db            # schema + dữ liệu
python -m ml.train_match         # lr-v1 (nhãn yếu, chia train/test theo ngành)
python -m ml.train_salary       # RandomForest vs baseline trung vị
python -m pytest -q             # 35 test (cần Postgres đã seed)
python -m ml.evaluate           # -> reports/metrics.json
cd .. && python scripts/gen_report.py   # -> docs/bao-cao-danh-gia.md/.docx
python scripts/gen_docs.py              # -> docs/01-yeu-cau-va-thiet-ke.md
python scripts/check_counts.py          # kiểm tra số bản ghi
```

## Tài liệu

- [docs/01-yeu-cau-va-thiet-ke.md](docs/01-yeu-cau-va-thiet-ke.md): yêu cầu, ERD, bảng truy vết (sinh tự động)
- [docs/bao-cao-danh-gia.md](docs/bao-cao-danh-gia.md): báo cáo đánh giá hiệu quả gợi ý (sinh từ `reports/metrics.json`)
- [docs/huong-dan-cham-nhan.md](docs/huong-dan-cham-nhan.md): hướng dẫn chấm nhãn người (kiểm chứng điểm khớp)
- [docs/qa/](docs/qa/): 8 ảnh chụp luồng vàng; `python scripts/qa_screenshots.py` chụp lại
- [PLAN-KHA-THI.md](PLAN-KHA-THI.md), [PROGRESS.md](PROGRESS.md): kế hoạch và nhật ký thi công

## Dữ liệu thật và mô phỏng

Thật: nội dung tin (tên việc, mô tả, yêu cầu, kỹ năng, lương, địa điểm) từ VietJobs.
Mô phỏng: ngày đăng tin, công ty, ứng viên, đơn ứng tuyển và kết quả qua vòng (seed 42, cột `is_simulated`).
Các chart dựa trên phần mô phỏng đều ghi "(mô phỏng)". Chi tiết và hạn chế trong báo cáo đánh giá.

> Các file `QUICKSTART.md`, `RUN.md`, `DOCKER_*.md`, `GETTING_STARTED.md`, `PLAN-BI-AI-JOB-SYSTEM.md`... là tư liệu của phiên bản cũ (Celery/Redis, dữ liệu mock), không còn đúng.
