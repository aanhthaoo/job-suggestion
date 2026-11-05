# Báo cáo đánh giá hiệu quả gợi ý

*Sinh tự động bởi `scripts/gen_report.py` từ `reports/metrics.json` ngày 2026-11-02. Số liệu không gõ tay.*

## 1. Phương pháp

**Matching Score** là điểm 0-1 cho mỗi cặp (ứng viên, tin), tính từ 7 đặc trưng: độ phủ kỹ năng có trọng số (`skill_cov`),
độ tương đồng văn bản TF-IDF (từ 1-2 gram và ký tự 3-5 gram), mức đáp ứng kinh nghiệm, học vấn, địa điểm, lương mong muốn và
mức khớp cấp bậc hai chiều (`level_fit`, phạt cả ứng viên thiếu lẫn thừa cấp).
Hai bộ chấm điểm được so sánh: `heuristic-v1` (tổng có trọng số cố định) và `lr-v1` (hồi quy logistic học từ nhãn yếu).
Mô hình mặc định đang dùng: **lr-v1**.

**Nhãn yếu để huấn luyện lr-v1.** Mẫu dương là ứng viên giả lập lấy 50-80% kỹ năng của một tin, thêm 1-3 kỹ năng nhiễu,
kinh nghiệm lệch ±1 năm. Mẫu âm khó là tin cùng ngành nhưng khác cấp bậc hoặc trùng dưới 30% kỹ năng; mẫu âm dễ là tin khác ngành.
Để tránh học vẹt, **chia train/test theo ngành**: mô hình không thấy 4 ngành kiểm tra (Công nghệ thông tin, Tài chính - Kế toán, Logistics - Vận tải, Xây dựng - Kiến trúc).

**Bài toán xếp hạng để đánh giá.** Với 400 ứng viên kiểm tra, xếp hạng 1242 tin của các ngành giữ lại.
Một tin được coi là liên quan nếu same category+level, |exp diff|<=1, job-job skill Jaccard>=0.4 (synthetic labels); trung bình mỗi ứng viên có 10.9 tin liên quan.
Mỗi chỉ số kèm khoảng tin cậy 95% bằng bootstrap 1000 lần trên ứng viên (seed 42).

## 2. Dữ liệu: phần thật và phần mô phỏng

| Thành phần | Nguồn | Thật hay mô phỏng |
|---|---|---|
| Tên việc, mô tả, yêu cầu, kỹ năng kỹ thuật, mức lương, địa điểm, kinh nghiệm | VietJobs (HuggingFace `dinhieufam/VietJobs`), mẫu ≤ 5000 dòng, giữ tin có ≥ 2 kỹ năng | **Thật** |
| Ngày đăng tin (`posted_at`) | Rải đều 12 tháng, seed 42 (VietJobs không có cột ngày) | **Mô phỏng** |
| Công ty | Sinh theo ngành (VietJobs không có cột công ty) | **Mô phỏng** |
| Ứng viên, kỹ năng ứng viên | Lấy mẫu theo phân bố kỹ năng của tin cùng ngành | **Mô phỏng** |
| Đơn ứng tuyển và kết quả qua vòng | Xác suất sigmoid theo Matching Score, seed 42 | **Mô phỏng** |

Hệ quả: các biểu đồ xu hướng theo thời gian và mọi chỉ số tuyển dụng (funnel, tỷ lệ qua vòng) **không phản ánh thị trường thật**;
chúng chứng minh hệ thống vận hành đúng, không chứng minh hiệu quả thực tế. Các chart liên quan đều ghi "(mô phỏng)".

## 3. Kết quả

### 3.1 Phân loại cặp (AUC trên ngành giữ lại)

| Mô hình | AUC |
|---|---|
| skill_cov đơn lẻ | 0.9667 |
| heuristic-v1 | 0.9856 |
| lr-v1 | 0.9896 |

### 3.2 Xếp hạng (trung bình [khoảng tin cậy 95%])

| Phương pháp | P@5 | Recall@10 | MRR | nDCG@10 |
|---|---|---|---|---|
| Ngẫu nhiên | 0.009 [0.005; 0.013] | 0.012 [0.008; 0.017] | 0.037 [0.027; 0.048] | 0.010 [0.006; 0.014] |
| Chỉ TF-IDF | 0.097 [0.082; 0.112] | 0.145 [0.124; 0.167] | 0.219 [0.192; 0.248] | 0.122 [0.104; 0.140] |
| Chỉ độ phủ kỹ năng | 0.191 [0.165; 0.215] | 0.344 [0.305; 0.381] | 0.345 [0.310; 0.378] | 0.276 [0.247; 0.305] |
| heuristic-v1 (6 đặc trưng, trọng số cố định) | 0.312 [0.284; 0.340] | 0.514 [0.477; 0.550] | 0.601 [0.564; 0.639] | 0.461 [0.431; 0.494] |
| lr-v1 (hồi quy logistic) | 0.316 [0.290; 0.343] | 0.519 [0.483; 0.553] | 0.629 [0.596; 0.665] | 0.471 [0.441; 0.499] |

**Nhận xét.** Cả hai bộ chấm điểm vượt xa ngẫu nhiên và vượt xa từng đặc trưng đơn lẻ, cho thấy việc kết hợp kỹ năng với
kinh nghiệm, học vấn, địa điểm có ích. TF-IDF đơn lẻ yếu hơn độ phủ kỹ năng vì văn bản ứng viên chỉ gồm danh sách kỹ năng. lr-v1 nhỉnh hơn heuristic-v1 về giá trị trung bình nhưng các khoảng tin cậy 95% chồng lên nhau, nên chưa thể kết luận chắc chắn mô hình học tốt hơn trọng số cố định.
Giá trị tuyệt đối còn thấp (P@5 khoảng 0.32) vì tập liên quan định nghĩa chặt (cùng cấp bậc, kinh nghiệm sát,
kỹ năng chồng lấn ≥ 40%) trong khi nhiều tin cùng ngành gần như tương đương với ứng viên.

Hệ số lr-v1 (đặc trưng đã chuẩn hóa 0-1): skill_cov = 12.197, text_sim = 4.343, exp_fit = 1.375, edu_fit = 8.956, loc_fit = 2.294, salary_fit = 2.303, level_fit = 3.643. Hệ số `edu_fit` lớn phản ánh
cách sinh nhãn (mẫu dương luôn đủ học vấn), không nên diễn giải như tầm quan trọng trong thực tế.

**Sửa lỗi cấp bậc (trước/sau).** Lần đánh giá đầu cho thấy mô hình gán điểm cao cho tin khác cấp bậc vì `exp_fit` chỉ phạt một phía.
Mình thêm đặc trưng `level_fit` rồi huấn luyện và đánh giá lại với cùng seed:

| Mô hình | Chỉ số | Trước (6 đặc trưng) | Sau (7 đặc trưng, có level_fit) |
|---|---|---|---|
| heuristic-v1 | P@5 | 0.275 | 0.312 |
| heuristic-v1 | MRR | 0.548 | 0.601 |
| heuristic-v1 | nDCG@10 | 0.403 | 0.461 |
| lr-v1 | P@5 | 0.282 | 0.316 |
| lr-v1 | MRR | 0.584 | 0.629 |
| lr-v1 | nDCG@10 | 0.419 | 0.471 |

Cảnh báo công bằng: tập "liên quan" của bài đánh giá có điều kiện *cùng cấp bậc*, nên đặc trưng mới được hưởng lợi một phần do cách đặt nhãn.
Cải thiện này chưa phải bằng chứng trên dữ liệu thật.

### 3.3 Độ nhạy của điểm

Thêm 1 kỹ năng còn thiếu: điểm tăng trung bình +0.064, không giảm ở 100% trường hợp (n = 172).
Bớt 1 kỹ năng đã khớp: điểm đổi trung bình -0.458, không tăng ở 100% trường hợp (n = 200).
Điểm đơn điệu theo kỹ năng, đúng kỳ vọng.

### 3.4 Độ trễ API (100 request, gọi trong tiến trình, kể cả truy vấn Postgres)

| Endpoint | p50 (ms) | p95 (ms) |
|---|---|---|
| GET /recommendations?k=20 | 51.6 | 73.8 |
| GET /jobs/{id}/match | 35.0 | 55.8 |
| GET /jobs (with match_score) | 43.8 | 64.7 |

### 3.5 Mô hình ước lượng lương

Tập kiểm tra 544 tin (chia theo hash `job_key`), đơn vị triệu VND/tháng.

| Mô hình | MAE | MAPE |
|---|---|---|
| Trung vị theo (ngành, cấp bậc) | 4.626 | 31.2% |
| RandomForest | 4.683 | 30.3% |

RandomForest **không** tốt hơn baseline về MAE, nên API trả trung vị phân khúc làm ước lượng chính và chỉ kèm dự đoán RandomForest để tham khảo.
Lương trong VietJobs nhiễu và nhiều tin không công khai lương, nên sai số quanh 31% là hợp lý.

### 3.6 Tỷ lệ qua vòng theo nhóm điểm khớp (mô phỏng)

| Nhóm điểm | Số đơn | Qua phỏng vấn | Nhận offer |
|---|---|---|---|
| <0.55 | 917 | 4.8% | 1.7% |
| 0.55-0.75 | 179 | 29.1% | 15.6% |
| >=0.75 | 1525 | 48.4% | 33.7% |

**Lưu ý quan trọng:** kết quả này là **vòng lặp tự xác nhận**: xác suất qua vòng trong dữ liệu mô phỏng được sinh từ chính Matching Score,
nên nhóm điểm cao đương nhiên qua vòng nhiều hơn. Bảng chỉ kiểm tra pipeline (điểm -> đơn -> funnel -> chart) chạy thông, không phải bằng chứng hiệu quả tuyển dụng thật.

### 3.7 Kiểm chứng bằng người

1 người chấm, 20 cặp (điểm trung bình các người chấm, thang 1-5). Hệ số Spearman giữa điểm người và điểm mô hình là **0.769** (p = 0.0001). Quy ước đọc: ≥ 0,6 khá tốt; 0,3-0,6 trung bình; dưới 0,3 yếu (xem `docs/huong-dan-cham-nhan.md`).

Chi tiết: người chấm cho các cặp mô hình xếp cao nhất trung bình **4.0/5**, các cặp ở mức giữa danh sách **1.8/5**. Trong 10 cặp mô hình xếp hạng 1, **60%** được người chấm ≥ 4 điểm (đây là con số chuẩn xác theo người, so với mục tiêu 85%). Riêng trong nhóm xếp cao, Spearman = 0.73 (p = 0.017).

**Lưu ý khi diễn giải:** (1) chỉ 1 người chấm với 20 cặp, nên khoảng bất định lớn; (2) bộ cặp gồm một nửa xếp cao và một nửa xếp giữa, nên Spearman tổng thể được nâng lên nhờ phân biệt hai nhóm dễ; mức đồng thuận trong nhóm xếp cao (số trên) mới phản ánh khả năng chọn đúng tin tốt nhất; (3) các cặp lệch lớn thường là tin khác ngành vẫn được điểm cao (ví dụ kho/logistics với ứng viên xây dựng) hoặc tin cấp quản lý bị chấm thấp dù người chấm thấy phù hợp.

## 4. Đối chiếu 4 chỉ số mục tiêu (slide 10)

| Chỉ số mục tiêu | Mục tiêu | Đo được | Kết luận |
|---|---|---|---|
| Độ chuẩn xác gợi ý | 85% | P@5 = 31.6% (nhãn tổng hợp, tập liên quan định nghĩa chặt) | **Chưa đạt** theo nhãn tổng hợp; theo nhãn người: 60% số tin xếp hạng 1 được người chấm ≥ 4 điểm (n = 10, 1 người chấm) - vẫn chưa đạt 85% |
| Sai số dự báo lương | ±10% | MAPE tốt nhất = 30.3% (MAE 4.626 triệu) | **Chưa đạt**; lương trong VietJobs nhiễu và là dải rộng |
| Tỷ lệ qua vòng lọc khi điểm cao | 3,2 lần | 10.1 lần (qua phỏng vấn, điểm ≥ 0,75 so với < 0,55) | Số này sinh từ dữ liệu **mô phỏng tự xác nhận** (mục 3.6), **không** dùng làm bằng chứng đạt |
| Thời gian phản hồi | dưới 5 giây | p95 gợi ý = 73.8 ms | **Đạt** |

Kết luận trung thực: chỉ chỉ số thời gian phản hồi được chứng minh. Hai chỉ số chất lượng (chuẩn xác, sai số lương) đã đo thật nhưng **chưa đạt** mục tiêu;
chỉ số tỷ lệ qua vòng không đo được trên dữ liệu thật vì không có đơn ứng tuyển thật.

Về các nhóm yêu cầu chức năng của đề bài: Matching Score có giải thích; phân tích CV (parser, CV health, gợi ý sửa CV bằng Gemini có fallback);
2 dashboard Superset (15 chart, đều trả dữ liệu) và KPI nhà tuyển dụng lọc theo công ty; tìm kiếm, lọc, gợi ý top-K và xếp hạng ứng viên. Các chức năng này đều chạy được.

## 5. Phân tích lỗi: 3 ví dụ mô hình sai

**Ví dụ 1.** Ứng viên sinh từ tin *Nhân Viên Thiết Kế 3D Nội Thất (Xây dựng - Kiến trúc, Junior)* với kỹ năng Figma, Photoshop, SketchUp, Vi tính văn phòng. Mô hình xếp hạng 1 tin *UI Artist (Công nghệ thông tin, Mid)* với điểm 1.00 (khớp: Figma, Photoshop). Tin này không thuộc tập liên quan vì khác ngành (mô hình chưa có đặc trưng khớp ngành, chỉ dựa vào kỹ năng chung).

**Ví dụ 2.** Ứng viên sinh từ tin *Nhân Viên Thiết Kế (Công nghệ thông tin, Junior)* với kỹ năng AI, Kế Toán Tổng Hợp, PowerPoint, Đọc Và Hiểu Bản Vẽ Kỹ Thuật. Mô hình xếp hạng 1 tin *Chuyên Viên Tài Chính (Lương Cứng: 15 - 22 Triệu) (Tài chính - Kế toán, Mid)* với điểm 0.92 (khớp: PowerPoint). Tin này không thuộc tập liên quan vì khác ngành (mô hình chưa có đặc trưng khớp ngành, chỉ dựa vào kỹ năng chung).

**Ví dụ 3.** Ứng viên sinh từ tin *Kiến Trúc Sư (Xây dựng - Kiến trúc, Mid)* với kỹ năng Lumion, Node.js, Phân Tích Thị Trường, Revit. Mô hình xếp hạng 1 tin *Họa Viên Revit (Công nghệ thông tin, Mid)* với điểm 1.00 (khớp: Lumion, Revit). Tin này không thuộc tập liên quan vì khác ngành (mô hình chưa có đặc trưng khớp ngành, chỉ dựa vào kỹ năng chung).

Trong 3 ví dụ: 3 lỗi khác ngành, 0 lỗi khác cấp bậc. Lỗi khác ngành xảy ra khi ứng viên có kỹ năng dùng chung nhiều ngành (Photoshop, Revit, Tin học văn phòng...) và nhãn ngành của VietJobs thô; mô hình chưa có đặc trưng khớp ngành giữa `candidate.major` và `category` của tin.

## 6. Hạn chế

- Nhãn huấn luyện và đánh giá đều tổng hợp; chưa có nhãn người (xem 3.7). Con số xếp hạng có thể lạc quan so với dữ liệu thật.
- Dữ liệu ứng viên, đơn ứng tuyển, công ty, ngày đăng là mô phỏng; kết quả BI về thời gian và funnel chỉ có giá trị minh họa.
- Văn bản ứng viên chỉ gồm tên kỹ năng và ngành, chưa dùng toàn văn CV, nên đặc trưng TF-IDF yếu.
- Chưa có đặc trưng khớp ngành (ứng viên so với tin); đã thêm `level_fit` nhưng đánh giá cấp bậc dùng nhãn tổng hợp (xem mục 3.2).
- Từ vựng kỹ năng gồm 140 mục chuẩn hóa từ VietJobs, nhiều mục là kỹ năng mềm; thiếu bao phủ cho kỹ năng kỹ thuật hiếm.
- Gemini chỉ dùng cho gợi ý sửa CV; chất lượng phụ thuộc quota và model miễn phí, luôn có fallback mẫu.

## 7. Hướng phát triển

Embedding đa ngôn ngữ và pgvector; đặc trưng khớp ngành (`field_fit`); skill graph; thu nhãn thật từ nhà tuyển dụng (nhấp, mời phỏng vấn) để huấn luyện lại;
quét ATS và lập lịch ETL; cookie httpOnly, audit log; nhúng Superset bằng guest token; E2E tự động và load test song song.
