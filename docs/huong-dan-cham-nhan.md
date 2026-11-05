# Hướng dẫn chấm nhãn người (kiểm chứng Matching Score)

**Mục đích.** Mọi con số xếp hạng trong báo cáo hiện dựa trên nhãn tổng hợp (do máy sinh). Bạn chấm tay 20 cặp (ứng viên, tin) để kiểm tra
điểm của mô hình có khớp với đánh giá của người hay không. Kết quả là một hệ số Spearman đưa vào báo cáo.

**Thời gian:** khoảng 15-20 phút cho 20 dòng. **Không cần** biết mô hình chấm bao nhiêu điểm (cố ý giấu để không bị ảnh hưởng).

---

## 1. Chuẩn bị

1. Mở file `reports/label_me.csv` bằng **Excel** (bấm đúp). File đã lưu UTF-8 có BOM nên tiếng Việt hiển thị đúng.
   Nếu chữ bị lỗi: Excel → Data → From Text/CSV → chọn *65001: Unicode (UTF-8)*.
2. Mỗi dòng là một cặp. Cột cần điền: **`human_score_1_to_5`** (cột cuối, đang trống). Đừng sửa các cột khác, đừng đổi `pair_id`.
3. File `reports/label_me_key.csv` chứa điểm của mô hình: **không mở** trước khi chấm xong.

## 2. Đọc một dòng

Hãy tưởng tượng bạn là nhà tuyển dụng vừa nhận CV này cho tin kia. Các cột:

| Nhóm | Cột | Ý nghĩa |
|---|---|---|
| Ứng viên | `candidate_major`, `candidate_skills`, `candidate_exp_years`, `candidate_education`, `candidate_location`, `candidate_expected_salary_trieu` | Ngành, kỹ năng, số năm kinh nghiệm, học vấn, nơi ở, lương mong muốn (triệu VND/tháng) |
| Tin | `job_title`, `job_category`, `job_level`, `job_skills`, `job_exp_min`, `job_location`, `job_salary_max_trieu` | Vị trí, ngành, cấp bậc, kỹ năng yêu cầu, kinh nghiệm tối thiểu, địa điểm, lương tối đa |

## 3. Thang điểm 1-5

Chấm theo câu hỏi: **"Nhà tuyển dụng có nên mời ứng viên này phỏng vấn cho tin này không?"**

| Điểm | Nghĩa | Dấu hiệu thường gặp |
|---|---|---|
| **5** | Rất phù hợp, mời phỏng vấn ngay | Có hầu hết kỹ năng yêu cầu; cùng ngành; kinh nghiệm đủ; cấp bậc hợp; cùng địa điểm |
| **4** | Phù hợp | Thiếu 1 kỹ năng nhỏ hoặc lệch nhẹ (địa điểm khác nhưng cùng vùng, kinh nghiệm thiếu ít) |
| **3** | Cân nhắc | Khớp khoảng một nửa kỹ năng, hoặc khớp kỹ năng nhưng lệch cấp bậc / địa điểm đáng kể |
| **2** | Ít phù hợp | Chỉ trùng kỹ năng chung (Tin học văn phòng, giao tiếp...) hoặc khác ngành nhưng có điểm chung |
| **1** | Không phù hợp | Khác ngành, không có kỹ năng cốt lõi, hoặc lệch cấp bậc nghiêm trọng (thực tập sinh vào vị trí trưởng phòng) |

**Cách cân nhắc các yếu tố** (theo thứ tự quan trọng):
1. **Kỹ năng cốt lõi** (so `candidate_skills` với `job_skills`): quan trọng nhất. Kỹ năng chung chung (Tin học văn phòng, Kỹ năng giao tiếp) chỉ tính ít.
2. **Cùng ngành** (`candidate_major` so `job_category`).
3. **Kinh nghiệm và cấp bậc** (`candidate_exp_years` so `job_exp_min` và `job_level`): thiếu nhiều thì giảm điểm; dư nhiều (ứng viên giàu kinh nghiệm xin vị trí thực tập) cũng giảm.
4. **Địa điểm và lương**: ảnh hưởng nhỏ, chỉ dùng để phân biệt khi hai yếu tố trên ngang nhau.

**Ví dụ minh họa** (không nằm trong file):

| Ứng viên | Tin | Điểm | Lý do |
|---|---|---|---|
| Kỹ năng Python, SQL, Docker; 3 năm; Hà Nội | Backend Developer; cần Python, SQL, Docker, Git; ≥ 2 năm; Hà Nội | 5 | Khớp gần đủ, cùng cấp, cùng nơi |
| Python, SQL; 1 năm; Hà Nội | Senior Backend; cần Python, SQL, Docker, K8s; ≥ 5 năm | 2 | Có kỹ năng nhưng thiếu kinh nghiệm và cấp bậc quá xa |
| Photoshop, Illustrator; 2 năm | Kế toán tổng hợp; cần Excel, phần mềm kế toán | 1 | Khác ngành, không có kỹ năng cốt lõi |

## 4. Quy tắc để nhãn đáng tin

- **Chấm theo nội dung dòng đó**, không suy đoán thêm. Đừng so sánh với dòng trước.
- **Dùng toàn bộ thang 1-5**, tránh chấm toàn 3. Nếu phân vân giữa hai mức, chọn mức thấp hơn.
- **Chỉ số nguyên** (hoặc để trống nếu không thể quyết định); giá trị ngoài 1-5 bị bỏ qua.
- Chấm một mạch, không dừng giữa chừng quá lâu, để tiêu chí nhất quán.
- Cần **ít nhất 10 dòng** có điểm thì hệ thống mới tính kết quả; nên chấm đủ 20.

## 5. Nhiều người chấm (khuyến nghị 2-3 người)

Một người chấm dễ lệch cá nhân. Để tăng độ tin cậy:

1. Mỗi người **sao chép** `label_me.csv` thành file riêng cùng thư mục `reports/`, đặt tên `label_me_<tên>.csv`, ví dụ `label_me_an.csv`, `label_me_binh.csv`.
2. Mỗi người chấm **độc lập**, không trao đổi trước khi xong.
3. Hệ thống tự gộp: lấy **điểm trung bình** của các người chấm cho từng cặp, và tính thêm **độ đồng thuận giữa các người chấm**.
   (File gốc `label_me.csv` cũng được tính là một người chấm nếu có điền.)

## 6. Chạy tính kết quả

Từ thư mục dự án:

```bash
cd backend
python -m ml.evaluate            # tính Spearman, ghi vào reports/metrics.json
cd ..
python scripts/gen_report.py     # cập nhật mục 3.7 của docs/bao-cao-danh-gia.md và .docx
```

Đừng dùng `--relabel` (lệnh này tạo lại bộ 20 cặp mới và **xóa nhãn đã chấm**).

## 7. Đọc kết quả

Mục 3.7 trong `docs/bao-cao-danh-gia.md` sẽ ghi số người chấm, số cặp, hệ số **Spearman ρ** giữa điểm người và điểm mô hình, giá trị p,
và (nếu ≥ 2 người) độ đồng thuận giữa người chấm.

| ρ | Nhận định |
|---|---|
| ≥ 0,6 | Điểm mô hình khá tương quan với đánh giá của người |
| 0,3 - 0,6 | Tương quan trung bình: mô hình có ích nhưng còn sai lệch đáng kể |
| < 0,3 | Yếu: không nên tin điểm mô hình khi chưa cải thiện |

Lưu ý khi diễn giải:
- Với chỉ 20 cặp, khoảng bất định lớn; **giá trị p < 0,05** mới coi là có bằng chứng thống kê.
- Nếu **độ đồng thuận giữa người chấm** thấp (dưới ~0,5), nghĩa là chính con người cũng không thống nhất; khi đó ρ của mô hình khó vượt cao hơn mức đó.
- Báo cáo ghi kết quả thật, kể cả khi thấp. ρ thấp là phát hiện hữu ích để cải thiện mô hình (ví dụ thêm đặc trưng khớp ngành), không phải lỗi của bạn.

## 8. Câu hỏi thường gặp

- **Tại sao có cặp trông rất khác ngành?** Bộ 20 cặp gồm 10 cặp mô hình xếp cao nhất và 10 cặp ở mức giữa danh sách của 10 ứng viên, để có cả trường hợp tốt lẫn kém.
- **Tôi không hiểu một kỹ năng.** Tra nhanh trên mạng hoặc bỏ trống dòng đó.
- **Lỡ sửa nhầm cột khác?** Khôi phục bằng cách chạy `python -m ml.evaluate --relabel` (mất toàn bộ nhãn đã chấm) hoặc dùng lịch sử Git nếu đã commit.
