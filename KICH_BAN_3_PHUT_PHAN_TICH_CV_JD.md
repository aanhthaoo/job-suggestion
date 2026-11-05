# KỊCH BẢN THUYẾT TRÌNH DEMO HỆ THỐNG: PHÂN TÍCH CV, KHỚP JD VÀ XÁC ĐỊNH SKILL GAPS

Thời lượng: Khoảng 3 phút.
Phương thức thực hiện: Thao tác trực tiếp trên trình duyệt web tại địa chỉ http://localhost:3000, không cần mở code hay terminal.

---

## PHẦN 1: CHỌN VÀ PHÂN TÍCH CV THỰC TẾ (Thời gian: 0:00 - 0:45)

[Hành động giao diện]
1. Mở trình duyệt tại trang đăng nhập: http://localhost:3000/auth/login.
2. Bấm nút 1-Click "Ứng viên Demo" để đăng nhập nhanh.
3. Trên thanh điều hướng trên cùng, bấm chọn mục "Hồ sơ & CV" để vào trang: http://localhost:3000/profile.
4. Tại khu vực tải CV, bấm tải lên file CV thực tế cv_huong_linh.docx (hoặc chọn sẵn CV thực tế của ứng viên Tạ Thu Hương Linh).
5. Cuộn xuống để xem kết quả bóc tách tự động và tab Chẩn đoán sức khỏe CV.

[Lời thoại thuyết trình]
Kính thưa quý thầy cô và các bạn. Hôm nay em xin trình bày giải pháp ứng dụng mô hình AI và Business Intelligence để giải quyết bài toán định hướng nghề nghiệp cho sinh viên thông qua một hồ sơ thực tế.

Trên màn hình là CV thực tế của bạn Tạ Thu Hương Linh, sinh viên năm 3 chuyên ngành Công nghệ thông tin tại Đại học Phenikaa Hà Nội. Mục tiêu nghề nghiệp của bạn là tìm kiếm vị trí Thực tập sinh hoặc Fresher Lập trình Web Frontend.

Khi tải CV lên hệ thống, bộ phân tích tự động trích xuất các thông tin cốt lõi mà không cần nhập tay: từ thông tin liên hệ, học vấn, số năm kinh nghiệm là 0 năm, cho đến danh mục các kỹ năng kỹ thuật hiện có như React, JavaScript, HTML, CSS, Tailwind CSS, ExpressJS, MySQL và Git. Đồng thời, hệ thống chấm điểm sức khỏe CV định lượng và chỉ ra ngay những điểm cần hoàn thiện về số liệu đo lường.

---

## PHẦN 2: TÌM KIẾM JD PHÙ HỢP VỚI MỤC TIÊU NGHỀ NGHIỆP (Thời gian: 0:45 - 1:25)

[Hành động giao diện]
1. Trên thanh menu, bấm chọn mục "Việc làm" để vào trang: http://localhost:3000/jobs.
2. Tại ô tìm kiếm từ khóa, nhập tên tin tuyển dụng: Phần mềm fullstack tươi hơn (hoặc gõ từ khóa: tươi hơn).
3. Hệ thống lọc ra tin tuyển dụng mã số ID 244 của Công ty An Phát (đơn vị liên kết đào tạo dự án cùng CMC Global).
4. Bấm trực tiếp vào thẻ tin để mở trang chi tiết việc làm: http://localhost:3000/jobs/244.
5. Lướt nhanh qua phần Mô tả công việc và Yêu cầu ứng viên.

[Lời thoại thuyết trình]
Tiếp theo, để tìm kiếm một tin tuyển dụng phù hợp với mục tiêu của ứng viên, em chuyển sang trang Việc làm và tìm kiếm vị trí: Phần mềm fullstack tươi hơn, mã tin ID 244.

Đây là một mô tả công việc hoàn toàn thực tế trong tập dữ liệu VietJobs. Do bản dịch tự động, chữ "Fresher" được dịch là "tươi hơn", nhưng nội dung bài đăng chính là chương trình đào tạo kỹ sư lập trình Fresher của CMC Global tại Hà Nội. Tin tuyển dụng này yêu cầu kinh nghiệm là 0 năm, ưu tiên sinh viên công nghệ thông tin sắp hoặc mới tốt nghiệp, hoàn toàn trùng khớp với định hướng thực tập sinh của bạn Hương Linh tại Hà Nội.

---

## PHẦN 3: ÁP DỤNG MÔ HÌNH AI PHÂN TÍCH VÀ XÁC ĐỊNH SKILL GAPS (Thời gian: 1:25 - 2:15)

[Hành động giao diện]
1. Tại trang chi tiết http://localhost:3000/jobs/244, nhìn sang cột bên phải tại mục "Vì sao khớp?".
2. Chỉ con trỏ chuột vào chỉ số điểm khớp tổng thể: 90.9% (Mức Cao).
3. Chỉ vào các thanh tiến trình của 7 đặc trưng matching: Độ phủ kỹ năng, Độ tương đồng ngữ nghĩa, Kinh nghiệm, Học vấn, Địa điểm, Cấp bậc và Mức lương.
4. Chỉ vào dòng chữ màu xanh các kỹ năng đã khớp: React, JavaScript, HTML, CSS.
5. Chỉ vào dòng cảnh báo chữ màu đỏ nổi bật: "Kỹ năng còn thiếu" gồm SQL, Java, Python, C#.

[Lời thoại thuyết trình]
Ngay khi mở trang tin, mô hình Matching AI 7 thành phần của hệ thống đã tự động đối sánh hồ sơ của ứng viên với yêu cầu của JD và đưa ra kết quả phân tích rất minh bạch.

Điểm tương thích tổng thể đạt mức 90.9%, thuộc phân loại Cao. Hệ thống chỉ ra ứng viên đã khớp trọn vẹn 4 kỹ năng nền tảng của giao diện Web là React, JavaScript, HTML và CSS, đồng thời đạt tuyệt đối về mức độ phù hợp địa điểm tại Hà Nội và cấp bậc Fresher.

Quan trọng nhất, mô hình AI đã bóc tách chính xác 4 khoảng trống kỹ năng, tức Skill Gaps, mà ứng viên đang thiếu so với tiêu chuẩn của nhà tuyển dụng. Bốn kỹ năng đó là: SQL, Java, Python và C#. 

Đối với một lập trình viên web hướng tới lộ trình Fullstack, việc CV chỉ mới dừng ở mức làm việc cơ bản với MySQL mà thiếu đi kỹ năng truy vấn SQL chuẩn mực, cũng như chưa có một ngôn ngữ hướng đối tượng backend vững chắc như Java hay Python, chính là rào cản lớn nhất khiến ứng viên có thể bị loại ở vòng phỏng vấn kỹ thuật.

---

## PHẦN 4: ĐỀ XUẤT TÁI CẤU TRÚC OUTLINE CV KHẮC PHỤC SKILL GAPS (Thời gian: 2:15 - 3:00)

[Hành động giao diện]
1. Ở cột bên phải, bấm vào nút "Gợi ý sửa CV theo tin (AI)".
2. Hệ thống tải và mở ra khối "Gợi ý tối ưu CV".
3. Chỉ vào phần "Từ khóa nên thêm vào CV" và "Gợi ý viết lại thành tích".

[Lời thoại thuyết trình]
Để giúp ứng viên khắc phục ngay các skill gaps này, em bấm vào nút "Gợi ý sửa CV theo tin". Module AI lập tức đưa ra khuyến nghị cụ thể để tái cấu trúc lại Outline CV như sau:

Thứ nhất, tại mục Kỹ năng kỹ thuật: Cần đưa từ khóa SQL lên vị trí nổi bật. Thay vì chỉ ghi MySQL chung chung, ứng viên cần nêu rõ năng lực viết truy vấn SQL, thiết kế lược đồ quan hệ và tối ưu hóa câu lệnh.

Thứ hai, tại mục Dự án thực tế: Tái cấu trúc lại 2 dự án thương mại điện tử và hệ thống đấu giá theo mô hình STAR. Cần bổ sung các gạch đầu dòng nêu rõ: ứng viên đã dùng SQL để quản lý bảng dữ liệu đơn hàng và người dùng ra sao, cũng như kết nối RESTful API giữa giao diện React với backend như thế nào, kèm theo số liệu đo lường cụ thể.

Thứ ba, tại mục Mục tiêu nghề nghiệp: Bổ sung định hướng học tập một ngôn ngữ hướng đối tượng backend tiêu chuẩn như Java hoặc Python để sẵn sàng tham gia chương trình đào tạo của doanh nghiệp.

Bằng việc bám sát giao diện thực tế và các khuyến nghị định lượng của mô hình AI, ứng viên có thể nâng cấp CV một cách bài bản, biến các điểm thiếu sót thành lợi thế cạnh tranh khi ứng tuyển.

Em xin kết thúc phần trình bày, cảm ơn quý thầy cô đã chú ý theo dõi.
