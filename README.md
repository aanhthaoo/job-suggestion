# JobPortal - Hệ Thống Tìm Việc Làm Thông Minh

Đồ án môn Business Intelligence - Đại học Thủy Lợi

## Công nghệ Stack

### Frontend
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS + shadcn/ui components
- TanStack Query (React Query)
- Zustand (state management)

### Backend
- FastAPI (Python 3.11)
- PostgreSQL 16 + pgvector
- Redis + Celery (background tasks)
- Apache Superset (BI dashboards)

## Cài đặt và Chạy

### Cách 1: Chạy với Docker Compose (Recommended)

```bash
# Clone repository
cd job-suggestion

# Start tất cả services
docker compose up -d

# Kiểm tra status
docker compose ps

# Xem logs
docker compose logs -f frontend
docker compose logs -f backend
```

Truy cập:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Superset: http://localhost:8088

### Cách 2: Chạy local (Development)

#### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tài khoản Demo

### Admin
- Email: `admin@test.com`
- Password: `admin123`

### User
- Email: `user@test.com`
- Password: `user123`

## Cấu trúc Project

```
job-suggestion/
├── frontend/              # Next.js frontend
│   ├── app/              # Pages (App Router)
│   ├── components/       # React components
│   ├── lib/              # Utilities, API client
│   └── mock/             # Mock data
├── backend/              # FastAPI backend
│   ├── app/
│   │   └── main.py       # Main application
│   └── requirements.txt
├── docker/               # Docker configs
├── data/                 # Data files (VietJobs, etc.)
├── docker-compose.yml    # Docker services
└── README.md
```

## Tính năng

### Phase 1: Giao diện (Hoàn thành)
- ✅ Trang chủ với search bar
- ✅ Danh sách việc làm với filters
- ✅ Chi tiết việc làm
- ✅ Quản lý hồ sơ cá nhân
- ✅ Admin dashboard

### Phase 2: Backend API (Đang phát triển)
- ✅ Authentication (JWT)
- ✅ CRUD APIs cho Jobs, Users
- ⏳ File upload (CV PDF/DOCX)
- ⏳ Background tasks (Celery)

### Phase 3: Smart Features
- ⏳ CV parsing (OCR + NER)
- ⏳ Auto-matching score
- ⏳ Personalized recommendations

### Phase 4: Data Pipeline
- ⏳ VietJobs dataset ingestion
- ⏳ Greenhouse API integration
- ⏳ ETL pipeline
- ⏳ Superset dashboards

## API Documentation

Swagger UI: http://localhost:8000/docs

## Troubleshooting

### Lỗi port đã được sử dụng
```bash
# Kiểm tra port đang dùng
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Dừng containers
docker compose down
```

### Lỗi database connection
```bash
# Restart PostgreSQL
docker compose restart postgres

# Xem logs
docker compose logs postgres
```

### Reset toàn bộ
```bash
docker compose down -v
docker compose up -d
```

## Liên hệ

Email: support@jobportal.vn

---

**Lưu ý:** Đây là bản demo cho mục đích học tập. Không sử dụng cho production.
