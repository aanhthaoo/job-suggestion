# Hướng dẫn chạy với Docker - One Command Setup

## 🚀 Chạy toàn bộ hệ thống (1 lệnh duy nhất)

```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose up
```

**Đợi 2-5 phút** để build và start tất cả services.

Sau đó truy cập:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **Superset:** http://localhost:8088 (admin/admin)

---

## 📋 Kiểm tra status

Mở terminal mới:

```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose ps
```

Bạn sẽ thấy 7 services đang chạy:
- `job-suggestion-postgres-1` → PostgreSQL database
- `job-suggestion-redis-1` → Redis cache
- `job-suggestion-backend-1` → FastAPI backend
- `job-suggestion-worker-1` → Celery worker
- `job-suggestion-beat-1` → Celery Beat scheduler
- `job-suggestion-frontend-1` → Next.js frontend
- `job-suggestion-superset-1` → Apache Superset BI

---

## 🔍 Xem logs

### Xem tất cả logs:
```bash
docker compose logs -f
```

### Chỉ xem frontend:
```bash
docker compose logs -f frontend
```

### Chỉ xem backend:
```bash
docker compose logs -f backend
```

### Chỉ xem worker (Celery):
```bash
docker compose logs -f worker
```

---

## 🛑 Dừng hệ thống

### Tạm dừng (giữ data):
```bash
docker compose down
```

### Dừng + Xóa hết data (reset hoàn toàn):
```bash
docker compose down -v
```

---

## 🎯 Demo flow sau khi chạy Docker

### Bước 1: Mở trang chủ
```
http://localhost:3000
```
- Thấy search bar, stats, featured jobs

### Bước 2: Login
```
Email: user@test.com
Password: user123
```

### Bước 3: Tìm kiếm việc làm
```
http://localhost:3000/jobs
```
- Filter theo "Python", "Hà Nội"
- Click vào job để xem chi tiết

### Bước 4: Xem gợi ý cá nhân hóa
```
http://localhost:3000/recommendations
```
- Thấy jobs phù hợp với kỹ năng user
- Match score badges hiển thị

### Bước 5: Admin Dashboard
```
Login: admin@test.com / admin123
URL: http://localhost:3000/admin/dashboard
```
- System health (PostgreSQL, Redis, Celery)
- Background tasks monitoring
- Click "Đồng bộ ngay" để trigger sync

### Bước 6: API Documentation
```
http://localhost:8000/docs
```
- Swagger UI với tất cả endpoints
- Test APIs trực tiếp

### Bước 7: Superset BI Dashboards
```
http://localhost:8088
Login: admin / admin
```
- Tạo dashboards analytics
- Connect đến PostgreSQL để query data

---

## 🔧 Troubleshooting

### Lỗi: Port đã được sử dụng

**Kiểm tra port nào đang bị chiếm:**
```bash
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :8088
```

**Kill process:**
```bash
taskkill /PID <PID> /F
```

**Hoặc đổi port trong docker-compose.yml:**
```yaml
ports:
  - "3001:3000"  # Đổi 3000 thành 3001
```

### Lỗi: Build failed

**Xóa cache và build lại:**
```bash
docker compose down
docker system prune -a
docker compose build --no-cache
docker compose up
```

### Lỗi: Frontend không load được

**Xem logs:**
```bash
docker compose logs frontend
```

**Thường là do chưa cài xong node_modules, đợi thêm 1-2 phút**

### Lỗi: Backend không connect được database

**Kiểm tra PostgreSQL đã ready:**
```bash
docker compose logs postgres | grep "ready to accept connections"
```

**Restart backend:**
```bash
docker compose restart backend
```

### Lỗi: Out of memory

**Tăng RAM cho Docker Desktop:**
1. Mở Docker Desktop Settings
2. Resources → Advanced
3. Tăng Memory lên 8GB+

**Hoặc giảm số services (tạm thời tắt Superset):**
Comment out superset service trong docker-compose.yml

---

## 📊 Resource Usage

Khi chạy đầy đủ 7 services:
- **RAM:** ~4.5 - 6GB
- **CPU:** 2-4 cores
- **Disk:** ~3GB (images + volumes)

---

## 🎓 Giải thích kiến trúc Docker

```
┌─────────────────────────────────────────────┐
│           Docker Network                     │
│                                              │
│  ┌──────────┐    ┌──────────┐               │
│  │ Frontend │───▶│ Backend  │               │
│  │ (Next.js)│    │(FastAPI) │               │
│  └──────────┘    └────┬─────┘               │
│                       │                      │
│                  ┌────┴─────┐               │
│                  │          │                │
│            ┌─────▼──┐  ┌───▼────┐           │
│            │Postgres│  │ Redis  │           │
│            │   DB   │  │ Cache  │           │
│            └────────┘  └────────┘           │
│                                              │
│  ┌──────────┐    ┌──────────┐               │
│  │  Worker  │    │   Beat   │               │
│  │ (Celery) │    │(Scheduler)               │
│  └──────────┘    └──────────┘               │
│                                              │
│  ┌──────────┐                               │
│  │ Superset │                               │
│  │   (BI)   │                               │
│  └──────────┘                               │
└─────────────────────────────────────────────┘
```

**Luồng dữ liệu:**
1. User truy cập Frontend (port 3000)
2. Frontend gọi Backend API (port 8000)
3. Backend query PostgreSQL (port 5432)
4. Background tasks chạy qua Celery Worker
5. Celery Beat trigger scheduled tasks mỗi 12h
6. Superset đọc data từ PostgreSQL để tạo dashboards

---

## 💡 Tips & Tricks

### Chạy chỉ một số services:
```bash
# Chỉ chạy frontend + backend
docker compose up frontend backend

# Chỉ chạy database + redis
docker compose up postgres redis
```

### Execute command trong container:
```bash
# Vào shell của backend container
docker compose exec backend bash

# Chạy Python REPL trong backend
docker compose exec backend python

# Query PostgreSQL
docker compose exec postgres psql -U postgres -d jobportal
```

### Rebuild chỉ một service:
```bash
# Rebuild frontend
docker compose build frontend
docker compose up -d frontend

# Rebuild backend
docker compose build backend
docker compose up -d backend
```

### Xem resource usage:
```bash
docker stats
```

---

## ✅ Checklist trước khi demo

- [ ] Docker Desktop đang chạy
- [ ] `docker compose up` đã chạy thành công
- [ ] Truy cập được http://localhost:3000
- [ ] Truy cập được http://localhost:8000/docs
- [ ] Login được với user@test.com / user123
- [ ] Login được với admin@test.com / admin123
- [ ] Trang /jobs hiển thị danh sách việc làm
- [ ] Trang /recommendations hiển thị gợi ý
- [ ] Admin dashboard hiển thị system health

Nếu tất cả ✅ → Sẵn sàng demo!

---

**Liên hệ:** support@jobportal.vn
