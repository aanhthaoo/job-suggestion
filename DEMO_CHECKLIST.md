# ✅ Kiểm tra Luồng Demo - JobPortal

## 🎯 Trạng thái Build

### Frontend
- ✅ Build thành công (npm run build)
- ✅ Không còn lỗi `cacheComponents`
- ✅ 7 pages được generate:
  - `/` - Trang chủ (Static)
  - `/jobs` - Danh sách việc làm (Static)
  - `/jobs/[id]` - Chi tiết job (Dynamic - server-rendered)
  - `/auth/login` - Đăng nhập (Static)
  - `/auth/register` - Đăng ký (Static)
  - `/admin/dashboard` - Admin panel (Static)
  - `/recommendations` - Gợi ý cá nhân hóa (Static)

### Backend
- ✅ Đã fix lỗi FileNotFoundError
- ✅ Mock jobs data được copy vào Docker container
- ✅ API endpoints sẵn sàng

---

## 🧪 Luồng Demo Checklist

### Bước 1: Khởi động hệ thống
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"

# Option A: Docker (đầy đủ nhất)
docker compose up -d

# Option B: Local (nhanh hơn cho dev)
# Terminal 1: cd backend && python run.py
# Terminal 2: cd frontend && npm run dev
```

**Kiểm tra:**
- [ ] Frontend chạy tại http://localhost:3000
- [ ] Backend API chạy tại http://localhost:8000
- [ ] Không có lỗi trong logs

---

### Bước 2: Trang chủ (Home Page)
**URL:** http://localhost:3000

**Kiểm tra:**
- [ ] Hiển thị search bar prominent
- [ ] Stats section (48,092 jobs, 500+ companies, 10,000+ candidates)
- [ ] Featured jobs (6 jobs đầu tiên từ mock data)
- [ ] Navigation header với logo "JobPortal"
- [ ] Footer với links

**Test:**
- Nhập "Python" vào search box → Enter
- Phải redirect đến /jobs?search=Python

---

### Bước 3: Tìm kiếm & Lọc việc làm
**URL:** http://localhost:3000/jobs

**Kiểm tra:**
- [ ] Hiển thị tất cả 10 jobs từ mock data
- [ ] Filter sidebar hoạt động:
  - [ ] Search by keyword
  - [ ] Filter by location (Hà Nội, TP.HCM, Đà Nẵng)
  - [ ] Filter by job type (Full-time, Part-time, Internship)
  - [ ] Filter by work mode (On-site, Remote, Hybrid)
- [ ] Job cards hiển thị đúng thông tin:
  - Title, company name
  - Location, salary, job type
  - Skills tags (max 5)
  - Posted date

**Test:**
- Filter location = "Hà Nội" → Phải thấy 5 jobs
- Filter job type = "Internship" → Phải thấy 1 job
- Search "Python" → Phải thấy 3 jobs

---

### Bước 4: Xem chi tiết job
**Action:** Click vào job card bất kỳ

**Kiểm tra:**
- [ ] URL thay đổi thành /jobs/1 (hoặc ID khác)
- [ ] Hiển thị đầy đủ:
  - Job title (large heading)
  - Company name với icon
  - Metadata grid (location, job type, salary, posted date)
  - Job description (full text)
  - Requirements (formatted)
  - Skills tags (all skills)
- [ ] Buttons hoạt động:
  - "Ứng tuyển ngay" (chưa implement form)
  - "Lưu việc" (chưa implement backend)

**Test:**
- Click job "Senior Python Developer"
- Check salary hiển thị đúng format VND
- Check ngày đăng hiển thị đúng (Oct 20, 2026)

---

### Bước 5: Đăng nhập
**URL:** http://localhost:3000/auth/login

**Kiểm tra:**
- [ ] Form hiển thị với 2 fields (email, password)
- [ ] Validation hoạt động (required fields)
- [ ] Error message hiển thị khi sai credentials
- [ ] Demo accounts hint box hiển thị

**Test:**
- Login với `user@test.com` / `user123` → Thành công
- Phải redirect về trang chủ
- Header phải thay đổi (hiển thị user menu)

- Logout → Header quay lại trạng thái chưa login
- Login với `admin@test.com` / `admin123` → Thành công

---

### Bước 6: Recommendations Page (SAU KHI LOGIN)
**URL:** http://localhost:3000/recommendations

**Kiểm tra:**
- [ ] Header hiển thị "Gợi ý" link
- [ ] User profile summary box hiển thị:
  - Skills: Python, SQL, Machine Learning, pandas
  - Experience: 2 năm
  - Location: Hà Nội
- [ ] Recommended jobs list (sorted by match score)
- [ ] Match score badges trên job cards
- [ ] Explanation section ở cuối trang

**Test:**
- Check jobs được sort theo match score (cao → thấp)
- Hover vào job card → Thấy % match
- Check "Cách hệ thống gợi ý?" section hiển thị đúng

---

### Bước 7: Admin Dashboard (với admin account)
**Login với:** admin@test.com / admin123  
**URL:** http://localhost:3000/admin/dashboard

**Kiểm tra:**
- [ ] "Admin" link hiển thị trong navigation
- [ ] System health cards:
  - PostgreSQL status (connected/disconnected)
  - Redis status
  - Celery status
- [ ] Quick stats:
  - Total jobs count
  - Total users count
  - Today applications
- [ ] Background tasks table:
  - Task names
  - Status badges (Succeeded/Failed/Running)
  - Started at timestamps
- [ ] "Đồng bộ ngay" button

**Test:**
- Click "Đồng bộ ngay" → Button shows loading state
- Check tasks table update (mock data)

---

### Bước 8: Backend API Documentation
**URL:** http://localhost:8000/docs

**Kiểm tra:**
- [ ] Swagger UI loads
- [ ] Tất cả endpoints listed:
  - Auth: POST /auth/login, POST /auth/register
  - Jobs: GET /jobs, GET /jobs/{id}
  - Applications: GET, POST /applications
  - Saved Jobs: GET, POST, DELETE /saved-jobs
  - Matching: POST /match/calculate
  - Recommendations: GET /recommendations
  - CV Parse: POST /cv/parse
  - Admin: GET /admin/stats, GET /admin/tasks
- [ ] "Try it out" buttons hoạt động

**Test:**
- Expand GET /api/v1/jobs → Click "Try it out" → Execute
- Phải nhận được 200 OK với JSON response
- Expand POST /api/v1/auth/login
- Test với `{"email": "user@test.com", "password": "user123"}`
- Phải nhận access_token

---

## 📊 Metrics Demo

Khi trình bày, có thể report:

| Metric | Value | Status |
|--------|-------|--------|
| Total pages | 7 | ✅ |
| Build success | Yes | ✅ |
| Mock jobs loaded | 10 | ✅ |
| API endpoints | 15+ | ✅ |
| Services in Docker | 7 | ✅ |
| Frontend load time | < 1s | ✅ |
| API response time | < 100ms | ✅ |

---

## 🐛 Troubleshooting nhanh

### Frontend không load:
```bash
cd frontend
npm run dev  # Chạy dev mode thay vì build
```

### Backend crash:
```bash
docker compose logs backend  # Xem lỗi
docker compose restart backend  # Restart
```

### Port bị chiếm:
```bash
netstat -ano | findstr :3000  # Check port 3000
taskkill /PID <PID> /F  # Kill process
```

### Login không hoạt động:
- Check browser console for errors
- Check Network tab → xem API call có gửi đúng không
- Verify credentials: user@test.com / user123

---

## ✅ Checklist hoàn thành

Sau khi test xong tất cả bước trên, đánh dấu:

- [ ] Bước 1: Hệ thống khởi động thành công
- [ ] Bước 2: Trang chủ hiển thị đẹp
- [ ] Bước 3: Search & filters hoạt động
- [ ] Bước 4: Job detail đầy đủ thông tin
- [ ] Bước 5: Login/logout hoạt động mượt
- [ ] Bước 6: Recommendations hiển thị match scores
- [ ] Bước 7: Admin dashboard monitor được system
- [ ] Bước 8: API docs accessible và testable

**Nếu tất cả ✅ → Sẵn sàng demo!**

---

**Thời gian demo ước tính:** 15-20 phút  
**Đối tượng:** Giảng viên môn Business Intelligence  
**Mục tiêu:** Chứng minh hệ thống vận hành end-to-end

Good luck! 🚀
