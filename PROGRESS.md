# PROGRESS (theo PLAN-KHA-THI.md)

## Trạng thái: 8/8 phiên XONG (2026-11-01)

| Phiên | Kết quả | Kiểm tra |
|---|---|---|
| 1 Nền | Bỏ redis/worker/beat/celery; routers `auth jobs cv candidate match applications employer admin`; upload uuid + pdf/docx + 5MB; JWT + bcrypt | `/health` 200; image backend build, stack `docker compose up` chạy |
| 2 Dữ liệu | `schema.sql` 11 bảng + 8 view; VietJobs thật 3573 tin/140 kỹ năng; 400 ứng viên + 2603 đơn mô phỏng (điểm khớp từ mô hình thật) | `python scripts/check_counts.py` OK |
| 3 Tài liệu | `docs/traceability.yaml` -> `scripts/gen_docs.py` -> `docs/01-yeu-cau-va-thiet-ke.md` (ERD sinh từ schema) | 20 FR + 6 NFR đều `done` |
| 4 CV | `cv_parser.py` viết lại; `ml/cv_health.py` 6 luật; 3 CV mẫu (health 100 / 51 / 3.6) | `tests/test_cv.py` |
| 5 Matching | `ml/matching.py` (6 đặc trưng, heuristic-v1 + lr-v1), `train_match`, `train_salary`, `cv_suggest` (Gemini + fallback), mọi API ở Mục 3.5 | `tests/test_matching.py`, `tests/test_flow.py` |
| 6 BI | `superset/bootstrap_superset.py`: 2 dashboard, 15 chart trên view; bootstrap tự kiểm tra mọi chart ≥ 1 hàng | `docker compose run --rm superset-init`: 15 OK, 0 FAIL; `/employer/kpi` 200 |
| 7 Frontend | Viết lại `lib/api.ts` + 11 trang (jobs, chi tiết, gợi ý, hồ sơ/CV, đơn, employer x3, admin); bỏ mock và `/saved` | `npm run build` OK; 8 ảnh `docs/qa/` bằng `scripts/qa_screenshots.py` |
| 8 Kiểm thử | `pytest -q` = 34 passed; `python -m ml.evaluate` -> `reports/metrics.json`; `scripts/gen_report.py` -> `docs/bao-cao-danh-gia.md/.docx` | xem báo cáo |

## Kết quả chính (từ reports/metrics.json, sau level_fit)
- Xếp hạng trên 4 ngành giữ lại: lr-v1 P@5 0.332, nDCG@10 0.489; heuristic-v1 P@5 0.327, nDCG@10 0.480; skill_cov 0.190/0.281; ngẫu nhiên ≈ 0. Khoảng tin cậy lr-v1 và heuristic chồng nhau: chưa kết luận được mô hình học tốt hơn.
- Mô hình lương: RandomForest (MAE 4.68) KHÔNG tốt hơn baseline trung vị (MAE 4.63) -> API trả trung vị phân khúc làm ước lượng chính.
- Độ trễ p95: recommendations 106 ms, match 55 ms (mục tiêu < 500 ms).

## Điểm lệch đã khắc phục
- Superset trỏ bảng cũ -> viết lại cho schema mới, dọn chart/dataset/dashboard cũ.
- `frontend/mock` và `/saved` -> đã xoá, UI không tự tính điểm.
- Điểm khớp trong đơn mô phỏng ban đầu là skill_cov -> chạy lại `etl.synth_applications --rebuild --engine` với lr-v1; hiệu chỉnh xác suất qua vòng (A=3.5) để tỷ lệ không bão hoà.
- sklearn trong container lệch host (pickle cảnh báo) -> ghim `scikit-learn==1.8.0`, pandas, numpy, joblib.
- Demo employer được gán công ty có nhiều đơn nhất để dashboard không trống.
- `.env` được `db.py` tự đọc khi chạy local.

## Vòng cải thiện 2 (2026-11-02)
- **level_fit** (đặc trưng thứ 7, phạt cấp bậc hai chiều) + sinh nhãn theo cấp bậc: lr-v1 P@5 0.282 -> 0.332, nDCG@10 0.419 -> 0.489 (bảng trước/sau trong báo cáo mục 3.2; số "trước" lưu ở `reports/metrics_before_level_fit.json`). Cảnh báo: tập liên quan có điều kiện cùng cấp bậc nên một phần cải thiện là do cách đặt nhãn.
- Lỗi còn lại của mô hình giờ là **khác ngành** (3/3 ví dụ): thiếu đặc trưng khớp ngành. Ghi vào hướng phát triển.
- **Funnel**: xác suất qua vòng thêm độ khó của tin và chất lượng ứng viên ngẫu nhiên (độc lập điểm khớp). Vẫn chỉ là mô phỏng, đã nêu rõ trong báo cáo.
- **Superset**: chart lương chính nay theo cấp bậc và ngành (lương thật); chart theo tháng giữ làm "minh họa, không phản ánh thị trường". 15/15 chart OK.
- **UI**: banner "Dữ liệu mô phỏng" ở employer dashboard, ứng viên xếp hạng, admin.
- **Nhãn người ĐÃ CHẤM (1 người, 20 cặp)**: Spearman 0.769 (p=0.0001); trong nhóm xếp cao 0.73 (p=0.017); 60% tin xếp hạng 1 được chấm ≥4 (mục tiêu slide 10: 85%). Cập nhật báo cáo mục 3.7 và 4. Hạn chế: 1 người chấm, n=20, bộ cặp gồm top+mid nên Spearman tổng thể được nâng.
- **Nhãn người (công cụ)**: `reports/label_me.csv` có thêm cột ngữ cảnh; hỗ trợ nhiều người chấm (`label_me_<tên>.csv`, lấy trung bình + độ đồng thuận); hướng dẫn chi tiết `docs/huong-dan-cham-nhan.md`. Chưa ai chấm.
- **Gemini**: chạy thật với key trong `.env`; `gemini-2.5-flash` đã bị Google gỡ cho tài khoản mới (404), `gemini-flash-latest` bị timeout; mặc định mới `gemini-flash-lite-latest` (~5 s), nguồn hiển thị `gemini`.
- Đã xem tinixai/vietnamese-job-descriptions (606k tin, có tên công ty): chỉ có NĂM đăng (không có tháng), không có kỹ năng cấu trúc, giấy phép CC BY-NC; KHÔNG dùng. Gán tên công ty thật cho tin không liên quan sẽ gây hiểu nhầm.

## Còn lại / giới hạn (ghi trong báo cáo)
- `posted_at`, công ty, ứng viên, đơn ứng tuyển là MÔ PHỎNG; xu hướng lương theo tháng phẳng vì ngày đăng rải đều. Không sửa được vì VietJobs không có các cột này.
- Funnel/tỷ lệ qua vòng là vòng lặp tự xác nhận (sinh từ chính điểm khớp); chỉ kiểm tra pipeline.
- Nhãn người mới có 1 người chấm; thêm 1-2 người (`label_me_<tên>.csv`) để có độ đồng thuận giữa người chấm.
- Báo cáo đối chiếu 4 chỉ số slide 10 (85% chuẩn xác, ±10% lương, 3,2x qua vòng, <5 s): chỉ thời gian phản hồi đạt; chuẩn xác và sai số lương chưa đạt; 3,2x không đo được trên dữ liệu thật.
