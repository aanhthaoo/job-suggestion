# Tài khoản Demo - JobPortal

## 🌐 Frontend (Next.js Web App)

### 1. Tài khoản Admin
```
Email: admin@test.com
Password: admin123
Role: admin
```

**Quyền hạn:**
- ✅ Xem tất cả jobs
- ✅ Ứng tuyển jobs
- ✅ Lưu jobs
- ✅ Upload CV
- ✅ **Truy cập Admin Dashboard** (`/admin/dashboard`)
- ✅ Monitor system health (PostgreSQL, Redis, Celery)
- ✅ View background tasks
- ✅ Trigger manual data sync
- ✅ Quản lý users và jobs

**Demo use case:**
- Show system monitoring capabilities
- Demonstrate admin controls
- View analytics and task status

---

### 2. Tài khoản User thường (Candidate)
```
Email: user@test.com
Password: user123
Role: candidate
```

**Quyền hạn:**
- ✅ Tìm kiếm việc làm
- ✅ Filter jobs (location, salary, job type, work mode)
- ✅ Xem chi tiết JD
- ✅ Ứng tuyển jobs
- ✅ Lưu jobs yêu thích
- ✅ Upload & quản lý CV
- ✅ Xem recommendations cá nhân hóa
- ✅ Theo dõi trạng thái applications

**Demo use case:**
- Normal user journey
- Search và filter jobs
- View personalized recommendations
- Apply to jobs

---

### 3. Tài khoản HR (Nhà tuyển dụng)
```
Email: hr@test.com
Password: hr123
Role: hr
```

**Quyền hạn:**
- ✅ Đăng tin tuyển dụng mới
- ✅ Quản lý jobs của công ty
- ✅ Xem applications cho jobs mình đăng
- ✅ Đổi trạng thái application (submitted → reviewed → interviewing → accepted/rejected)
- ✅ Xem danh sách candidates

**Demo use case:**
- Post new job
- Review applications
- Manage candidate pipeline

---

### 4. Tài khoản Demo khác (Optional)

#### Senior Developer Candidate
```
Email: senior.dev@test.com
Password: senior123
Role: candidate
Skills: Python, Django, PostgreSQL, Docker, AWS
Experience: 5 years
Location: Hà Nội
```

#### Fresher Candidate
```
Email: fresher@test.com
Password: fresher123
Role: candidate
Skills: JavaScript, React, Node.js
Experience: 0.5 years
Location: TP. Hồ Chí Minh
```

#### Intern Candidate
```
Email: intern@test.com
Password: intern123
Role: candidate
Skills: Python, SQL, Machine Learning
Experience: 0 years
Location: Hà Nội
```

---

## 📊 Apache Superset (BI Dashboard)

### Tài khoản mặc định
```
Username: admin
Password: admin
```

**Hoặc:**
```
Username: superset
Password: superset
```

### Cách setup lần đầu:

1. **Mở Superset:** http://localhost:8088
2. **Login** với admin/admin
3. **Create first dashboard:**
   - Click "Dashboards" → "+"
   - Name: "Job Market Overview"
   
4. **Connect to PostgreSQL:**
   - Settings → Database Connections
   - Add Database
   - SQLAlchemy URI: `postgresql://postgres:postgres123@postgres:5432/jobportal`
   - Test Connection → Save

5. **Create datasets:**
   - Datasets → + Dataset
   - Select table: `jobs`, `applications`, `users`

6. **Build charts:**
   - Charts → + Chart
   - Select dataset
   - Choose visualization type (Bar, Pie, Line, Map)
   - Configure metrics
   - Save & Add to Dashboard

### Dashboards nên tạo:

#### 1. Job Market Overview
- Total jobs by industry (Pie chart)
- Jobs by location (Map visualization)
- Average salary by position (Bar chart)
- Top 10 in-demand skills (Horizontal bar)
- Jobs trend over time (Line chart)

#### 2. User Activity Analytics
- Daily/Monthly active users (Line chart)
- Applications by status (Pie chart)
- Top companies by applications (Bar chart)
- User registration trend (Line chart)
- Conversion rate funnel (Funnel chart)

#### 3. Matching Quality Metrics
- Match score distribution (Histogram)
- Average match score by industry (Bar chart)
- Skills gap analysis (Heatmap)
- Recommendation accuracy (Gauge chart)
- Top missing skills (Word cloud)

---

## 🔧 Backend API Testing

### Swagger UI
```
URL: http://localhost:8000/docs
Không cần authentication để xem docs
```

### Test authenticated endpoints:

1. **Login first:**
   - Go to `/api/v1/auth/login`
   - Try it out with:
     ```json
     {
       "email": "user@test.com",
       "password": "user123"
     }
     ```
   - Copy the `access_token` from response

2. **Authorize in Swagger:**
   - Click "Authorize" button (padlock icon)
   - Enter: `Bearer YOUR_TOKEN_HERE`
   - Click "Authorize"

3. **Test protected endpoints:**
   - `/api/v1/users/me` - Get current user
   - `/api/v1/jobs` - List jobs
   - `/api/v1/applications` - Get applications
   - `/api/v1/admin/stats` - Admin stats (admin only)

---

## 📝 Quick Reference Card

| Service | URL | Username | Password | Purpose |
|---------|-----|----------|----------|---------|
| **Frontend** | http://localhost:3000 | user@test.com | user123 | Normal user demo |
| **Frontend Admin** | http://localhost:3000 | admin@test.com | admin123 | Admin dashboard |
| **Frontend HR** | http://localhost:3000 | hr@test.com | hr123 | Recruiter demo |
| **Backend API** | http://localhost:8000/docs | - | - | API documentation |
| **Superset** | http://localhost:8088 | admin | admin | BI dashboards |
| **PostgreSQL** | localhost:5432 | postgres | postgres123 | Database |
| **Redis** | localhost:6379 | - | - | Cache/Broker |

---

## 🎯 Demo Script với Accounts

### Kịch bản 1: User Journey (5 phút)
1. Login: `user@test.com` / `user123`
2. Homepage → Show featured jobs
3. Search "Python" + Filter "Hà Nội"
4. Click job → View details
5. Go to `/recommendations` → Show AI matching
6. Apply to a job
7. Check `/applications` → See status

### Kịch bản 2: Admin Monitoring (3 phút)
1. Login: `admin@test.com` / `admin123`
2. Go to `/admin/dashboard`
3. Show system health cards
4. View background tasks list
5. Click "Đồng bộ ngay" → Watch task run
6. Explain architecture

### Kịch bản 3: HR Workflow (3 phút)
1. Login: `hr@test.com` / `hr123`
2. Post new job (nếu có form)
3. View applications for company's jobs
4. Change application status
5. Review candidate profiles

### Kịch bản 4: BI Analytics (4 phút)
1. Open Superset: http://localhost:8088
2. Login: admin / admin
3. Show "Job Market Overview" dashboard
4. Drill into specific charts
5. Show real-time data updates
6. Explain data pipeline

---

## 🔐 Security Notes

**Đây là tài khoản demo, KHÔNG dùng cho production!**

- Passwords được hardcode trong code
- JWT secret là mock value
- Không có rate limiting
- Không có email verification
- Không có password hashing mạnh

**Cho production, cần:**
- bcrypt/argon2 password hashing
- Email verification flow
- Password reset mechanism
- Rate limiting
- CSRF protection
- HTTPS/SSL
- Environment variables cho secrets

---

## 💡 Tips

### Tạo thêm user mới:
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "password123",
    "full_name": "New User",
    "phone": "0123456789"
  }'
```

### Reset tất cả passwords:
Edit file `backend/app/main.py`, tìm `MOCK_USERS` dictionary và update passwords.

### Export user list:
```sql
-- PostgreSQL query
SELECT email, role, full_name, created_at 
FROM users 
ORDER BY created_at DESC;
```

---

**Last updated:** 2026-10-22  
**For questions:** support@jobportal.vn
