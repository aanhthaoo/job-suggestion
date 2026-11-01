# Hướng dẫn chạy nhanh - JobPortal

## Cách 1: Chạy với Docker Compose (Khuyến nghị)

### Bước 1: Đảm bảo Docker đang chạy
```bash
docker --version
docker compose version
```

### Bước 2: Start services
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose up -d
```

### Bước 3: Kiểm tra status
```bash
docker compose ps
```

Bạn sẽ thấy:
- `frontend` running on port 3000
- `backend` running on port 8000
- `postgres` running on port 5432
- `redis` running on port 6379
- `worker` running (Celery)
- `beat` running (Celery Beat scheduler)
- `superset` running on port 8088

### Bước 4: Truy cập
- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **Superset:** http://localhost:8088 (admin/admin)

### Xem logs
```bash
# Tất cả services
docker compose logs -f

# Chỉ frontend
docker compose logs -f frontend

# Chỉ backend
docker compose logs -f backend
```

### Dừng services
```bash
docker compose down
```

### Reset hoàn toàn (xóa data)
```bash
docker compose down -v
docker compose up -d
```

---

## Cách 2: Chạy local (Development)

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Truy cập: http://localhost:3000

### Backend

```bash
cd backend

# Tạo virtual environment (optional nhưng khuyến nghị)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
uvicorn app.main:app --reload
```

Truy cập: http://localhost:8000/docs

### PostgreSQL + Redis (qua Docker)

Nếu không muốn cài PostgreSQL và Redis locally, vẫn dùng Docker:

```bash
docker compose up -d postgres redis
```

Sau đó set environment variable cho backend:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobportal
REDIS_URL=redis://localhost:6379/0
```

---

## Tài khoản Demo

### Admin
- Email: `admin@test.com`
- Password: `admin123`
- Quyền: Vào được trang /admin/dashboard

### User thường
- Email: `user@test.com`
- Password: `user123`
- Quyền: Tìm kiếm, ứng tuyển, upload CV

---

## Test các tính năng

### 1. Trang chủ
- Vào http://localhost:3000
- Thấy search bar, featured jobs, stats

### 2. Tìm kiếm việc làm
- Vào http://localhost:3000/jobs
- Filter theo location, job type, work mode
- Click vào job để xem chi tiết

### 3. Đăng nhập
- Vào http://localhost:3000/auth/login
- Dùng tài khoản demo ở trên
- Sau khi login, header sẽ hiện menu user

### 4. Admin Dashboard
- Login với admin account
- Vào http://localhost:3000/admin/dashboard
- Xem system health, stats, background tasks

### 5. API Documentation
- Vào http://localhost:8000/docs
- Thử các endpoints trực tiếp từ Swagger UI

---

## Troubleshooting

### Lỗi: Port 3000 đã được sử dụng
```bash
# Tìm process đang dùng port 3000
netstat -ano | findstr :3000

# Kill process
taskkill /PID <PID> /F

# Hoặc đổi port trong docker-compose.yml
```

### Lỗi: Cannot connect to database
```bash
# Restart PostgreSQL
docker compose restart postgres

# Kiểm tra logs
docker compose logs postgres
```

### Frontend không load được
```bash
# Xóa node_modules và cài lại
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Backend không start được
```bash
# Kiểm tra logs
docker compose logs backend

# Thường là do chưa có PostgreSQL hoặc Redis running
docker compose up -d postgres redis
```

---

## Cấu trúc file quan trọng

```
job-suggestion/
├── docker-compose.yml          # Docker services config
├── README.md                   # Tài liệu chính
├── QUICKSTART.md              # File này
│
├── frontend/                   # Next.js app
│   ├── app/                   # Pages
│   │   ├── page.tsx           # Trang chủ
│   │   ├── jobs/page.tsx      # Danh sách việc làm
│   │   ├── jobs/[id]/page.tsx # Chi tiết job
│   │   ├── auth/login/page.tsx
│   │   ├── auth/register/page.tsx
│   │   └── admin/dashboard/page.tsx
│   ├── components/            # React components
│   │   ├── Header.tsx
│   │   └── JobCard.tsx
│   ├── lib/                   # Utilities
│   │   ├── api.ts             # API client
│   │   └── utils.ts
│   └── mock/                  # Mock data
│       └── jobs.json
│
├── backend/                    # FastAPI app
│   ├── app/
│   │   └── main.py            # Main application
│   ├── requirements.txt
│   └── Dockerfile
│
└── data/                       # Data files (sẽ thêm sau)
```

---

## Bước tiếp theo

Sau khi chạy thành công demo:

1. **Phase 2:** Implement backend đầy đủ với PostgreSQL
   - Database schema
   - Authentication với JWT
   - CRUD APIs thực sự

2. **Phase 3:** Thêm smart features
   - CV parsing
   - Matching algorithm
   - Recommendations

3. **Phase 4:** Data pipeline
   - Load VietJobs dataset
   - Integrate Greenhouse API
   - Setup Superset dashboards

Xem chi tiết trong `IMPLEMENTATION_PLAN.md`
