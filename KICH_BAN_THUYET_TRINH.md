# KỊCH BẢN BÁO CÁO BÀI TẬP LỚN
## HỆ THỐNG GỢI Ý VIỆC LÀM VÀ KẾT NỐI TUYỂN DỤNG THÔNG MINH (JOBPORTAL AI)
### Thời lượng: 12 - 15 phút
### Bố cục: Chia đôi màn hình (Split-Screen)
- Bên trái: Bảng checklist 5 yêu cầu cần báo cáo.
- Bên phải: Giao diện web thực tế (Next.js), Apache Superset, Swagger API và Tài liệu tương ứng.

---

## PHẦN MỞ ĐẦU (1.5 phút)

[Thao tác màn hình]
- Bên trái: Mở bảng checklist 5 yêu cầu.
- Bên phải: Mở trang chủ website http://localhost:3000 (giao diện tông màu pastel hồng nhạt và xanh dương).

[Lời thoại]
Chào thầy cô và các bạn. Hôm nay em xin phép đại diện nhóm báo cáo về bài tập lớn: Xây dựng hệ thống tìm kiếm việc làm và kết nối tuyển dụng thông minh JobPortal AI.

Để tiện theo dõi, em chia đôi màn hình:
- Nửa bên trái là danh sách 5 yêu cầu chính trong checklist của bài tập lớn.
- Nửa bên phải là sản phẩm web thực tế nhóm đã xây dựng và đang chạy trực tiếp trên máy.

Trong bài báo cáo này, em sẽ lần lượt đi qua từng yêu cầu trong checklist, đối chiếu trực tiếp với giao diện web, các tính năng thông minh và tài liệu đi kèm để chứng minh nhóm đã hoàn thành đầy đủ các yêu cầu đề ra.

Bây giờ em xin phép bắt đầu với yêu cầu đầu tiên.

---

## YÊU CẦU 1: PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ CƠ SỞ DỮ LIỆU (2.5 phút)

[Thao tác màn hình]
- Bên trái: Đánh dấu tích vào Yêu cầu 1.
- Bên phải: Mở file docs/01-yeu-cau-va-thiet-ke.md (cuộn đến phần sơ đồ ERD và bảng yêu cầu chức năng), sau đó mở nhanh tab hiển thị bảng cơ sở dữ liệu Postgres.

[Lời thoại]
Yêu cầu thứ nhất là phân tích yêu cầu hệ thống và thiết kế cơ sở dữ liệu cho ứng viên, nhà tuyển dụng và tin tuyển dụng.

Ở phần này, nhóm đã phân tích và chuẩn hóa hệ thống thành 20 yêu cầu chức năng cụ thể, được ghi chép chi tiết trong file tài liệu thiết kế ở nửa màn hình bên phải.

Về cơ sở dữ liệu, nhóm sử dụng PostgreSQL 16 kết hợp tiện ích pgvector, gồm 8 bảng dữ liệu chính:
- Bảng candidate lưu thông tin ứng viên, chuyên ngành, số năm kinh nghiệm, học vấn, điểm GPA và mức lương mong muốn.
- Bảng company và job_posting lưu thông tin doanh nghiệp và tin tuyển dụng chi tiết.
- Bảng skill, job_skill, candidate_skill lưu trữ danh mục kỹ năng chuyên môn, kỹ năng mềm và ma trận trọng số kỹ năng.
- Bảng cv_document lưu toàn văn văn bản CV và cấu trúc dữ liệu JSON đã bóc tách.
- Bảng application theo dõi trạng thái ứng tuyển theo phễu 4 giai đoạn.

Về nguồn dữ liệu: Nhóm tích hợp tập dữ liệu thật VietJobs với hơn 3.500 tin tuyển dụng từ thị trường việc làm Việt Nam. Nhóm đã xử lý dữ liệu để kéo về đầy đủ các trường thông tin quan trọng như quyền lợi đãi ngộ, giờ làm việc, loại hợp đồng và ngoại ngữ yêu cầu, giúp tin tuyển dụng rất chi tiết.

Để minh bạch: phần nội dung công việc, kỹ năng và mức lương là dữ liệu thật từ VietJobs; còn ngày đăng tin, tên công ty và các lượt ứng tuyển được sinh mô phỏng ngẫu nhiên (seed 42) để phục vụ việc huấn luyện mô hình và kiểm thử hệ thống.

---

## YÊU CẦU 2: XÂY DỰNG MÔ HÌNH AI PHÂN TÍCH CV VÀ TÍNH ĐIỂM TƯƠNG THÍCH (3.5 phút)

[Thao tác màn hình]
- Bên trái: Đánh dấu tích vào Yêu cầu 2.
- Bên phải: Vào trang đăng nhập http://localhost:3000/auth/login, bấm nút "Ứng viên Demo" -> Chuyển sang trang Hồ sơ & CV http://localhost:3000/profile.

[Lời thoại]
Yêu cầu thứ hai là xây dựng mô hình AI/Machine Learning để phân tích CV và tính toán điểm tương thích với mô tả công việc (Job Description).

Nhóm đã phát triển 2 phần tính năng thông minh cốt lõi:

Thứ nhất là tính năng bóc tách CV tự động và Chẩn đoán sức khỏe CV (CV Health Engine).
Hệ thống cho phép ứng viên tải lên file CV định dạng PDF hoặc DOCX (hỗ trợ tốt cả CV tiếng Việt lẫn tiếng Anh).
Khi tải lên, hệ thống tự động bóc tách thông tin liên hệ, học vấn, kinh nghiệm, dự án và nhận diện hơn 100 kỹ năng công nghệ.

[Thao tác màn hình]
- Chỉ vào thẻ điểm sức khỏe CV 78/100 trên trang profile.
- Bấm vào tab "Chẩn đoán Sức khỏe CV" để thấy 6 quy tắc và danh sách cảnh báo.
- Bấm thử nút "⚡ Thực tế (78đ)" và nút "⭐ Xuất sắc (100đ)" trên thanh công cụ để thấy điểm số và lỗi thay đổi trực tiếp.

[Lời thoại]
Điểm sức khỏe CV được chấm hoàn toàn định lượng trên thang điểm 100 dựa trên 6 quy tắc minh bạch:
1. Đủ các mục chính (20đ)
2. Thông tin liên hệ (15đ)
3. Độ phủ kỹ năng (15đ)
4. Số liệu thành tích định lượng (20đ)
5. Độ dài văn bản hợp lý từ 150 đến 700 từ (15đ)
6. Tránh các từ ngữ sáo rỗng (15đ)

Như thầy cô và các bạn thấy trên màn hình, mẫu CV thực tế này đạt 78 điểm. Hệ thống không chỉ chấm điểm mà còn chỉ ra cụ thể: CV mới có 2 số liệu định lượng (cần từ 4 số liệu trở lên), và phát hiện cụm từ sáo rỗng "nhiệt tình, ham học hỏi", đồng thời đưa ra lời khuyên để ứng viên sửa lại CV tốt hơn.

[Thao tác màn hình]
- Chuyển sang trang Việc làm gợi ý http://localhost:3000/recommendations.
- Bấm vào một tin tuyển dụng để mở trang chi tiết http://localhost:3000/jobs/1.

[Lời thoại]
Tính năng thông minh thứ hai là Thuật toán Matching Score có giải thích (Explainable AI Matching Engine).
Để điểm số có ý nghĩa và chính xác hơn việc đếm từ khóa thông thường, mô hình của nhóm kết hợp 7 đặc trưng:
1. Độ phủ kỹ năng có trọng số (skill_cov)
2. Độ tương đồng văn bản TF-IDF (text_sim)
3. Mức đáp ứng số năm kinh nghiệm (exp_fit)
4. Mức phù hợp học vấn (edu_fit)
5. Độ khớp địa điểm làm việc (loc_fit)
6. Mức khớp kỳ vọng lương (salary_fit)
7. Mức khớp cấp bậc hai chiều (level_fit) - giúp tránh việc ứng viên thiếu cấp bậc hoặc thừa trình độ quá xa so với công việc.

Ở trang chi tiết tin tuyển dụng bên phải, quý thầy cô và các bạn thấy điểm khớp đạt 89%. Hệ thống giải thích rất rõ ràng: ứng viên đã khớp những kỹ năng nào (hiển thị màu xanh lá) và còn thiếu những kỹ năng nào (hiển thị màu đỏ).

Ngoài ra, ở góc bên phải còn có Mô hình ước lượng khoảng lương thị trường (kết hợp mức lương trung vị phân khúc và mô hình Random Forest), giúp ứng viên biết mức lương tham khảo cho vị trí này.

---

## YÊU CẦU 3: THIẾT KẾ DASHBOARD BI TRỰC QUAN HÓA CÁC CHỈ SỐ (3 phút)

[Thao tác màn hình]
- Bên trái: Đánh dấu tích vào Yêu cầu 3.
- Bên phải: Chuyển sang trang Quản trị viên http://localhost:3000/admin/dashboard.

[Lời thoại]
Yêu cầu thứ ba là thiết kế Dashboard BI để trực quan hóa các chỉ số như số lượng ứng viên theo kỹ năng, xu hướng lương và tỷ lệ chuyển đổi tuyển dụng. Nhóm triển khai cả trên giao diện web và trên nền tảng chuyên dụng Apache Superset.

Trước hết là trên trang Quản trị của web:
- Nhóm xây dựng Biểu đồ Cung - Cầu kỹ năng Top 15: Cột xanh dương là số lượng ứng viên có kỹ năng đó, cột màu hồng là số lượng tin tuyển dụng yêu cầu. Nhìn vào biểu đồ có thể thấy ngay các kỹ năng đang có nhu cầu tuyển dụng vượt trội so với nguồn cung.
- Bên dưới là bảng phân tích Mức lương trung vị (Median Salary) theo từng ngành nghề.

[Thao tác màn hình]
- Đăng xuất, bấm nút 1-Click "Nhà tuyển dụng Demo" -> Vào trang http://localhost:3000/employer/dashboard.

[Lời thoại]
Với Nhà tuyển dụng:
Dashboard hiển thị 4 thẻ KPI đo lường hiệu quả: Tổng số đơn nộp, Tin đang mở, Tỷ lệ duyệt hồ sơ và Thời gian phản hồi trung bình.
Bên cạnh đó là Biểu đồ Phễu tuyển dụng theo dõi tỷ lệ chuyển đổi qua 4 vòng (Đã nộp -> Sàng lọc -> Phỏng vấn -> Offer), và biểu đồ thống kê các kỹ năng mà ứng viên ứng tuyển đang bị thiếu hụt nhiều nhất.

[Thao tác màn hình]
- Mở tab mới sang Apache Superset: http://localhost:8088 (đăng nhập admin/admin).
- Mở 2 Dashboard dựng sẵn: "Thị trường lao động" và "Hiệu quả tuyển dụng".

[Lời thoại]
Ngoài ra, nhóm triển khai Apache Superset chạy trên cổng 8088, kết nối trực tiếp với PostgreSQL.
Hệ thống có sẵn 2 Dashboard phân tích sâu:
- Dashboard Thị trường lao động: hiển thị cơ cấu lương theo cấp bậc, bản đồ nhiệt phân bố việc làm và ma trận tương quan kỹ năng.
- Dashboard Hiệu quả tuyển dụng: theo dõi chi tiết tỷ lệ chuyển đổi phễu theo từng bộ phận và thời gian tuyển dụng trung bình.

---

## YÊU CẦU 4: PHÁT TRIỂN GIAO DIỆN FRONTEND VÀ TÍCH HỢP API (2.5 phút)

[Thao tác màn hình]
- Bên trái: Đánh dấu tích vào Yêu cầu 4.
- Bên phải: Quay lại giao diện Web http://localhost:3000.

[Lời thoại]
Yêu cầu thứ tư là phát triển giao diện người dùng Frontend và tích hợp các API xử lý AI/BI vào hệ thống.

Về giao diện:
Toàn bộ frontend được xây dựng bằng Next.js App Router và Tailwind CSS. Nhóm thiết kế theo phong cách hiện đại với tông màu pastel Hồng nhạt và Xanh dương, giao diện sáng sủa và dễ sử dụng.

[Thao tác màn hình]
- Vào trang Tìm việc http://localhost:3000/jobs: Thử lọc theo địa điểm "Hà Nội" và loại hợp đồng "Toàn thời gian".
- Bấm vào 1 tin và bấm "Ứng tuyển ngay".
- Chuyển sang trang Tiến trình ứng tuyển http://localhost:3000/applications để thấy trạng thái đơn hàng và tiến trình phễu 4 bước.
- Thao tác nhanh: Đăng xuất, tạo một tài khoản mới bất kỳ -> Vào trang profile để cho thấy màn hình Empty State: hiển thị đúng tên tài khoản mới, điểm số hiển thị gạch ngang (--/100) và nhắc nộp CV, hoàn toàn không bị dính dữ liệu của người khác.

[Lời thoại]
Về tích hợp API:
Frontend giao tiếp mượt mà với Backend FastAPI qua hơn 25 API endpoint. Từ việc tra cứu việc làm, tính điểm matching theo thời gian thực, nộp đơn ứng tuyển, cho đến việc nhà tuyển dụng chuyển vòng ứng viên đều được đồng bộ tức thì xuống cơ sở dữ liệu.

[Thao tác màn hình]
- Mở tab Swagger Docs http://localhost:8000/docs để lướt qua danh sách API chuẩn OpenAPI.

---

## YÊU CẦU 5: KIỂM THỬ HỆ THỐNG VÀ VIẾT BÁO CÁO ĐÁNH GIÁ (2 phút)

[Thao tác màn hình]
- Bên trái: Đánh dấu tích vào Yêu cầu 5 (đã hoàn thành cả 5/5 yêu cầu).
- Bên phải: Mở file báo cáo docs/bao-cao-danh-gia.md.

[Lời thoại]
Yêu cầu cuối cùng là kiểm thử hệ thống với tập dữ liệu mẫu và viết báo cáo đánh giá hiệu quả của mô hình gợi ý.

Nhóm đã thực hiện kiểm nghiệm bài bản và tự động sinh ra file Báo cáo đánh giá khoa học ở nửa màn hình bên phải:
- Thử nghiệm trên 400 ứng viên kiểm thử và hơn 1.200 tin tuyển dụng được chia tách độc lập theo ngành.
- Kết quả xếp hạng: Mô hình AI đạt nDCG@10 là 0.471 và MRR là 0.629, vượt trội rất nhiều so với việc gợi ý ngẫu nhiên (nDCG = 0.010) hoặc chỉ dùng phương pháp TF-IDF đơn lẻ (nDCG = 0.122).
- Về độ nhạy của điểm số: Khi ứng viên học thêm 1 kỹ năng còn thiếu, điểm số tăng trung bình +0.064 và không giảm ở 100% các trường hợp thử nghiệm.
- Về hiệu năng: Thời gian phản hồi API khi tính matching cho 20 việc làm chỉ mất trung bình 51 mili-giây, đáp ứng tốt yêu cầu thời gian thực.
- Toàn bộ 14 test case tự động kiểm thử nghiệp vụ của backend đều vượt qua 100%.

---

## PHẦN KẾT THÚC (1 phút)

[Thao tác màn hình]
- Bên trái: Checklist hiển thị đầy đủ 5/5 mục đã hoàn thành.
- Bên phải: Quay lại trang chủ JobPortal AI.

[Lời thoại]
Tổng kết lại, qua phần trình bày vừa rồi kết hợp giữa bảng checklist yêu cầu và hệ thống web đang chạy thực tế, nhóm em đã hoàn thành trọn vẹn cả 5 yêu cầu của bài tập lớn:
1. Thiết kế cơ sở dữ liệu chuẩn hóa trên PostgreSQL cho hơn 3.500 tin tuyển dụng thật.
2. Xây dựng mô hình AI bóc tách CV, chẩn đoán sức khỏe CV định lượng và tính Matching Score có giải thích.
3. Thiết kế hệ thống Dashboard BI trên web và Apache Superset trực quan hóa toàn diện Cung - Cầu và Hiệu quả tuyển dụng.
4. Phát triển giao diện người dùng Next.js hiện đại, xử lý chỉn chu từ tài khoản mới đến ứng viên có CV.
5. Kiểm thử hệ thống và có báo cáo đánh giá định lượng đầy đủ với các chỉ số đo lường thực tế.

Bài báo cáo của nhóm em đến đây là kết thúc. Em xin cảm ơn thầy cô và các bạn đã chú ý lắng nghe. Nếu thầy cô và các bạn có câu hỏi hay thắc mắc gì thì em xin phép được giải đáp ạ.
