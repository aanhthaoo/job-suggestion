# HƯỚNG DẪN SỬ DỤNG VÀ KHỞI CHẠY HỆ THỐNG BẰNG DOCKER
### JobPortal AI — Nền Tảng Kết Nối Tuyển Dụng Thông Minh (AI Matching & Business Intelligence)

Tài liệu này hướng dẫn chi tiết từ A-Z cách cài đặt, khởi chạy, kiểm tra và trải nghiệm toàn bộ hệ thống bằng **Docker & Docker Compose** chỉ với một vài thao tác đơn giản.

---

## 📋 MỤC LỤC
1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Kiến trúc các dịch vụ trong Docker](#2-kiến-trúc-các-dịch-vụ-trong-docker)
3. [Hướng dẫn khởi chạy từng bước](#3-hướng-dẫn-khởi-chạy-từng-bước)
4. [Bảng địa chỉ truy cập dịch vụ](#4-bảng-địa-chỉ-truy-cập-dịch-vụ)
5. [Tài khoản demo & Đăng nhập 1-Click](#5-tài-khoản-demo--đăng-nhập-1-click)
6. [Kịch bản trải nghiệm tính năng nổi bật](#6-kịch-bản-trải-nghiệm-tính-năng-nổi-bật)
7. [Các lệnh quản trị Docker thường dùng](#7-các-lệnh-quản-trị-docker-thường-dùng)
8. [Chạy kiểm thử tự động hệ thống](#8-chạy-kiểm-thử-tự-động-hệ-thống)
9. [Xử lý sự cố thường gặp (Troubleshooting)](#9-xử-lý-sự-cố-thường-gặp-troubleshooting)

---

## 1. Yêu cầu hệ thống

Trước khi bắt đầu, máy tính của bạn cần đáp ứng các điều kiện sau:
- **Đã cài đặt Docker & Docker Compose**:
  - **Windows / macOS**: Cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/) (khuyến nghị bật chế độ WSL 2 backend trên Windows).
  - **Linux**: Docker Engine 24+ và Docker Compose v2.
- **Tài nguyên phần cứng khuyến nghị**:
  - RAM: Tối thiểu 4GB RAM trống (khuyến nghị 6GB - 8GB để chạy mượt cả Apache Superset).
  - Ổ đĩa: Tối thiểu 5GB dung lượng trống.
- **Kết nối mạng Internet**: Cần có mạng trong lần đầu chạy để Docker tải image và tự động kéo dataset `VietJobs.csv` từ Hugging Face.

---

## 2. Kiến trúc các dịch vụ trong Docker

Hệ thống được thiết kế dạng Microservices đồng bộ thông qua `docker-compose.yml`:

| Dịch vụ Container | Cổng Host | Công nghệ & Vai trò |
| :--- | :--- | :--- |
| **`postgres`** | `5432` | Cơ sở dữ liệu PostgreSQL 16 + pgvector, lưu trữ 3.575 tin tuyển dụng thật, ứng viên, đơn tuyển và hồ sơ CV. |
| **`backend`** | `8000` | FastAPI (Python 3.12) + scikit-learn: cung cấp REST API, bóc tách CV, chấm điểm CV Health 6 luật, thuật toán AI Matching 5 thành phần và mô hình dự đoán lương RandomForest. |
| **`frontend`** | `3000` | Next.js 16 (App Router, Tailwind CSS): giao diện người dùng hiện đại với tông màu Pastel Hồng nhạt & Xanh dương, hiển thị bản CV chuẩn ATS, kẹp sẵn 1-Click Login. |
| **`superset`** | `8088` | Apache Superset BI: Nền tảng phân tích trực quan dữ liệu lớn thị trường lao động và hiệu quả tuyển dụng. |
| **`superset-init`** | *(Nội bộ)* | Container tự động chạy 1 lần để thiết lập kết nối PostgreSQL, nạp cấu hình metrics, biểu đồ và 2 dashboard BI dựng sẵn. |

---

## 3. Hướng dẫn khởi chạy từng bước

### Bước 1: Mở thư mục dự án
Mở ứng dụng Terminal (macOS/Linux) hoặc PowerShell / Command Prompt (Windows) và chuyển vào thư mục dự án đã clone:
```bash
cd job-suggestion
```

### Bước 2: Tạo file cấu hình môi trường `.env`
Dự án đã chuẩn bị sẵn file `.env.example` với đầy đủ các cấu hình tiêu chuẩn:
- **Trên Windows (PowerShell / CMD)**:
  ```powershell
  copy .env.example .env
  ```
- **Trên Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

> **Ghi chú về Google Gemini API (Tùy chọn)**:  
> Trong file `.env`, trường `GEMINI_API_KEY` là tùy chọn. Nếu bạn không điền API key, hệ thống sẽ tự động kích hoạt bộ gợi ý Heuristic offline thông minh, đảm bảo 100% tính năng hoạt động trơn tru.

---

### Bước 3: Khởi chạy toàn bộ hệ thống bằng 1 lệnh duy nhất
Hãy đảm bảo Docker Desktop đang mở, sau đó chạy lệnh:
```bash
docker compose up -d --build
```

#### ⚙️ Cơ chế tự động diễn ra trong quá trình khởi động:
1. Docker tải các image cơ sở (`postgres`, `python`, `node`, `superset`) và build container.
2. `postgres` khởi động và kiểm tra sức khỏe (`healthcheck`).
3. Container `backend` tự động kích hoạt:
   - Chạy `python -m app.seed_db`: Khởi tạo cấu trúc bảng, tự động tải dataset `VietJobs.csv` từ Hugging Face nạp 3.575 tin tuyển dụng vào DB, tạo ứng viên và đơn tuyển mô phỏng, nạp tài khoản demo.
   - Chạy `python -m ml.train_match`: Huấn luyện mô hình AI Matching (Logistic Regression v1).
   - Chạy `python -m ml.train_salary`: Huấn luyện mô hình ước tính khoảng lương (Random Forest).
   - Khởi động máy chủ FastAPI tại cổng `8000`.
4. Container `frontend` build và chạy giao diện web tại cổng `3000`.
5. Container `superset` và `superset-init` dựng cơ sở dữ liệu BI và tạo 2 Dashboard trực quan tại cổng `8088`.

---

### Bước 4: Kiểm tra trạng thái hệ thống
Để kiểm tra xem các container đã chạy ổn định chưa, gõ lệnh:
```bash
docker compose ps
```
Nếu thấy các dịch vụ (`postgres`, `backend`, `frontend`, `superset`) đều hiển thị trạng thái `Up` (hoặc `healthy`) là hệ thống đã sẵn sàng 100%!

---

## 4. Bảng địa chỉ truy cập dịch vụ

Sau khi khởi chạy thành công, mở trình duyệt web và truy cập các địa chỉ sau:

| Dịch vụ | Địa chỉ URL | Mô tả chức năng |
| :--- | :--- | :--- |
| **Giao diện Web chính** | [http://localhost:3000](http://localhost:3000) | Cổng thông tin tìm việc, AI gợi ý việc làm, bản xem CV chuẩn ATS, KPI tuyển dụng |
| **Tài liệu API Backend (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Kiểm thử trực tiếp hơn 25 endpoint REST API tương tác với cơ sở dữ liệu và AI |
| **Apache Superset BI** | [http://localhost:8088](http://localhost:8088) | Dashboard trực quan hóa Cung - Cầu lao động, Lương Median và Phễu tuyển dụng |

---

## 5. Tài khoản demo & Đăng nhập 1-Click

Để việc nghiệm thu và chấm điểm bài tập lớn diễn ra nhanh nhất, tại trang đăng nhập [http://localhost:3000/auth/login](http://localhost:3000/auth/login), hệ thống đã tích hợp sẵn **3 nút "1-Click Đăng nhập Demo"**. Bạn chỉ cần bấm chuột vào nút tương ứng là đăng nhập ngay mà không cần nhập phím:

| Vai trò | Tài khoản Email | Mật khẩu | Tính năng chính trải nghiệm |
| :--- | :--- | :--- | :--- |
| **Ứng viên (Candidate)** | `candidate@demo.com` | `demo123` | • Xem bản CV chuẩn ATS 78đ<br>• Việc làm gợi ý AI (Matching Score %)<br>• Chẩn đoán sức khỏe CV 6 luật định lượng<br>• Quản lý tiến trình đơn ứng tuyển (Phễu 4 bước) |
| **Nhà tuyển dụng (Employer)** | `employer@demo.com` | `demo123` | • Dashboard KPI hiệu quả tuyển dụng<br>• AI Xếp hạng ứng viên theo độ khớp tin tuyển dụng<br>• Chuyển vòng tuyển dụng (Sàng lọc -> Phỏng vấn -> Offer)<br>• Đăng tin tuyển dụng đa thông tin (quyền lợi, giờ làm việc...) |
| **Quản trị viên (Admin)** | `admin@demo.com` | `demo123` | • Thống kê dữ liệu toàn sàn<br>• Biểu đồ Cung - Cầu kỹ năng Top 15<br>• Thống kê lương Median theo từng nhóm ngành |
| **Quản trị Superset BI** | `admin` | `admin` | • Đăng nhập tại `http://localhost:8088`<br>• Khám phá 2 Dashboard: `Thị trường lao động` & `Hiệu quả tuyển dụng` |

---

## 6. Kịch bản trải nghiệm tính năng nổi bật

### Kịch bản 1: Trải nghiệm Ứng viên (Candidate)
1. Truy cập [http://localhost:3000/auth/login](http://localhost:3000/auth/login) -> Bấm **"Ứng viên Demo"**.
2. **Khám phá việc làm (`/jobs`)**:
   - Sử dụng bộ lọc đa tiêu chí: Lọc theo thành phố (Hà Nội, TP.HCM...), mức lương, loại hợp đồng.
   - Bấm vào 1 tin bất kỳ (`/jobs/[id]`): Xem đầy đủ quyền lợi đãi ngộ (hộp quà 🎁), giờ làm việc, phân loại kỹ năng chuyên môn vs kỹ năng mềm và sidebar AI Matching Score.
3. **AI Gợi ý việc làm (`/recommendations`)**:
   - Xem danh sách việc làm được AI xếp hạng độ phù hợp `#1, #2, #3`.
   - Xem phân tích chi tiết: Kỹ năng trùng khớp (màu xanh) vs Kỹ năng cần học bổ sung (màu xám).
4. **Hồ sơ & Bản xem CV chuẩn ATS (`/profile`)**:
   - Tab **"Bản xem CV Chuẩn (Resume View)"**: Chiêm ngưỡng bản CV chuyên nghiệp chuẩn quốc tế với đầy đủ thông tin liên hệ, mục tiêu nghề nghiệp, kinh nghiệm làm việc theo timeline, dự án, học vấn, kỹ năng và chứng chỉ AWS/IELTS. Có nút **In / Xuất PDF**.
   - Tab **"Chẩn đoán Sức khỏe CV"**: Xem bảng điểm thực tế **78 / 100 điểm** phân bổ theo 6 quy tắc định lượng, xem các cảnh báo thực tế (thiếu số liệu định lượng, dùng từ sáo rỗng "nhiệt tình, ham học hỏi").
   - Thử nghiệm bấm vào các nút chuyển đổi mẫu nhanh: **⚡ Thực tế (78đ)**, **⭐ Xuất sắc (100đ)**, **⚠️ Cần sửa (51đ)** để thấy điểm số và matching thay đổi theo thời gian thực!
5. **Tiến trình đơn nộp (`/applications`)**:
   - Theo dõi thanh tiến trình chuyển đổi 4 giai đoạn trực quan: `Đã nộp -> Sàng lọc -> Phỏng vấn -> Nhận Offer`.

---

### Kịch bản 2: Trải nghiệm Nhà tuyển dụng (Employer)
1. Đăng xuất và đăng nhập bằng nút **"Nhà tuyển dụng Demo"**.
2. **Dashboard KPI (`/employer/dashboard`)**:
   - Quan sát 4 thẻ KPI: Tổng số đơn, Tin đang mở, Tỷ lệ duyệt hồ sơ, Thời gian tuyển dụng trung bình.
   - Xem biểu đồ phễu chuyển đổi ứng viên và top các kỹ năng mà ứng viên ứng tuyển còn thiếu hụt nhiều nhất.
3. **AI Xếp hạng Ứng viên (`/employer/candidates`)**:
   - Chọn một tin tuyển dụng: Hệ thống tự động xếp hạng ứng viên từ cao xuống thấp theo Matching Score.
   - Xem giải thích nguyên nhân điểm số, kỹ năng ứng viên đáp ứng và kỹ năng còn thiếu.
   - Thao tác đổi vòng tuyển dụng ngay trên giao diện (chuyển sang *Phỏng vấn* hoặc *Gửi Offer*).
4. **Đăng tin tuyển dụng mới (`/employer/jobs`)**:
   - Đăng bài tuyển dụng có đầy đủ các trường: Tiêu đề, Mức lương, Quyền lợi & Chế độ đãi ngộ, Giờ làm việc, Kỹ năng mềm, Ngoại ngữ yêu cầu.

---

### Kịch bản 3: Trải nghiệm Quản trị & Business Intelligence (BI)
1. Đăng nhập bằng nút **"Quản trị viên Demo"** -> Truy cập [http://localhost:3000/admin/dashboard](http://localhost:3000/admin/dashboard):
   - Xem số liệu tổng quan DB: Tổng số tin đăng, tổng ứng viên, tổng lượt ứng tuyển.
   - Biểu đồ đối chiếu **Cung - Cầu kỹ năng Top 15**: Cột xanh dương (Ứng viên) vs Cột hồng (Tin tuyển dụng) để tìm ra các kỹ năng đang "khát" nhân lực.
   - Bảng phân tích Lương trung vị (Median Salary) theo từng ngành nghề.
2. Truy cập [http://localhost:8088](http://localhost:8088) (Đăng nhập `admin` / `admin`):
   - Mở mục **Dashboards** -> Khám phá 2 bảng điều khiển chuyên sâu:
     - **Thị trường lao động**: Cơ cấu mức lương, bản đồ phân bố địa lý việc làm, ma trận kỹ năng.
     - **Hiệu quả tuyển dụng**: Phễu sàng lọc ứng viên, thời gian phản hồi đơn.

---

## 7. Các lệnh quản trị Docker thường dùng

Trong quá trình vận hành, bạn có thể sử dụng các lệnh Docker sau:

| Thao tác | Lệnh thực hiện |
| :--- | :--- |
| **Xem log trực tiếp của toàn hệ thống** | `docker compose logs -f` |
| **Xem log riêng của Backend** | `docker compose logs -f backend` |
| **Xem log riêng của Frontend** | `docker compose logs -f frontend` |
| **Khởi động lại một dịch vụ** | `docker compose restart backend` *(hoặc `frontend`)* |
| **Tạm dừng hệ thống (giữ nguyên dữ liệu)** | `docker compose stop` |
| **Bật lại hệ thống sau khi tạm dừng** | `docker compose start` |
| **Tắt và giải phóng các container** | `docker compose down` |
| **Xóa sạch và reset hoàn toàn dữ liệu ban đầu** | `docker compose down -v && docker compose up -d --build` |

---

## 8. Chạy kiểm thử tự động hệ thống (Automated Testing)

Dự án đã tích hợp sẵn bộ kiểm thử tự động toàn diện để phục vụ việc đánh giá, kiểm thử và demo:

### Cách 1: Chạy script kiểm thử tổng hợp (Khuyến nghị cho Demo)
Mở Terminal và gõ:
```bash
python scripts/run_tests.py
```
Lệnh này sẽ tự động:
1. Quét kiểm tra tính toàn vẹn 8 bảng cơ sở dữ liệu (3.575 tin tuyển dụng thật, 410 ứng viên, 2.621 đơn tuyển).
2. Chạy kiểm thử tự động cho bộ bóc tách CV (PDF/DOCX), 6 quy tắc CV Health và thuật toán AI Matching 7 đặc trưng.
3. Xuất bảng tổng kết kết quả kiểm thử (PASSED 100%).

### Cách 2: Chạy kiểm thử bằng Pytest
```bash
# Chạy toàn bộ 35 test cases
pytest backend/tests -v

# Hoặc chạy kiểm thử nhanh bộ giải thuật AI CV & Matching
pytest backend/tests/test_cv.py backend/tests/test_matching.py -v
```

### Cách 3: Chạy script đánh giá mô hình ML và sinh báo cáo
```bash
# Tính toán các chỉ số nDCG@10, P@5, MRR và độ trễ API
python backend/ml/evaluate.py

# Sinh lại file tài liệu Báo cáo đánh giá (docs/bao-cao-danh-gia.md & .docx)
python scripts/gen_report.py
```

---

## 9. Xử lý sự cố thường gặp (Troubleshooting)

### 1. Lỗi xung đột cổng (Port already allocated)
- **Hiện tượng**: Báo lỗi `Bind for 0.0.0.0:5432 failed: port is already allocated` hoặc tương tự với cổng 3000, 8000, 8088.
- **Nguyên nhân**: Máy tính đang có một ứng dụng khác (như PostgreSQL cục bộ, máy chủ web khác) chiếm dụng cổng đó.
- **Khắc phục**:
  - Tắt dịch vụ cục bộ đang chạy trên máy (ví dụ dừng PostgreSQL service trong Windows Services).
  - Hoặc chỉnh sửa cổng host trong file `docker-compose.yml` (ví dụ `"5433:5432"` cho postgres hoặc `"3001:3000"` cho frontend).

### 2. Docker Desktop chưa bật hoặc bị treo
- **Hiện tượng**: Lệnh `docker compose` báo lỗi `error during connect: ... open //./pipe/docker_engine: The system cannot find the file specified`.
- **Khắc phục**: Mở ứng dụng Docker Desktop trên máy và chờ biểu tượng góc dưới chuyển sang màu xanh lá cây (**Docker Desktop is running**).

### 3. Container Superset khởi động chậm
- **Hiện tượng**: Truy cập `http://localhost:8088` trong 1-2 phút đầu báo `502 Bad Gateway` hoặc chưa phản hồi.
- **Giải thích**: Apache Superset là một ứng dụng doanh nghiệp lớn, trong lần đầu tiên khởi chạy cần khoảng 60 - 90 giây để nâng cấp schema SQLite nội bộ và nạp metadata biểu đồ. Bạn chỉ cần chờ thêm 1 phút rồi F5 tải lại trang.

### 4. Mạng chập chờn khi tải dữ liệu VietJobs
- **Hiện tượng**: Log backend báo lỗi timeout khi download từ Hugging Face.
- **Khắc phục**: Kiểm tra kết nối mạng và chạy lệnh `docker compose restart backend`. Bộ nạp dữ liệu có cơ chế retry tự động.

---

> 🎉 **Chúc bạn có trải nghiệm tuyệt vời khi trải nghiệm và đánh giá hệ thống JobPortal AI!**  
> Mọi thắc mắc kỹ thuật vui lòng kiểm tra file tài liệu chi tiết tại thư mục `docs/`.

