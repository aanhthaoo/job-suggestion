# Sửa lỗi Docker Backend

## 🐛 Lỗi gặp phải

```
Traceback (most recent call last):
  File "/usr/local/bin/uvicorn", line 8, in <module>
    ...
ModuleNotFoundError hoặc import error
```

## ✅ Đã sửa gì?

1. **Giảm dependencies** - Loại bỏ spacy, sqlalchemy, pandas (không cần cho demo)
2. **Sửa Dockerfile** - Thêm healthcheck và proper install
3. **Cập nhật docker-compose.yml** - Thêm restart policy và explicit command
4. **Requirements tối ưu** - Chỉ giữ packages thực sự cần thiết

## 🚀 Chạy lại từ đầu (Clean Build)

### Bước 1: Dừng và xóa hết containers cũ
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"

# Dừng tất cả
docker compose down

# Xóa cache và images cũ
docker compose rm -f
docker system prune -f
```

### Bước 2: Build lại với cache mới
```bash
# Build chỉ backend trước để xem lỗi
docker compose build --no-cache backend

# Nếu thành công, build tất cả
docker compose build --no-cache
```

### Bước 3: Start toàn bộ
```bash
docker compose up
```

Hoặc chạy background:
```bash
docker compose up -d
```

### Bước 4: Kiểm tra logs
```bash
# Xem backend logs
docker compose logs -f backend

# Phải thấy:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔍 Kiểm tra từng service

### 1. Kiểm tra PostgreSQL
```bash
docker compose exec postgres pg_isready -U postgres
# Output: /tmp:5432 - accepting connections
```

### 2. Kiểm tra Redis
```bash
docker compose exec redis redis-cli ping
# Output: PONG
```

### 3. Kiểm tra Backend
```bash
# Test từ trong container
docker compose exec backend python -c "import requests; print(requests.get('http://localhost:8000/api/v1/jobs').json())"

# Hoặc test từ host
curl http://localhost:8000/api/v1/jobs
```

### 4. Kiểm tra Frontend
```bash
docker compose logs frontend | grep "Ready"
# Phải thấy: ✓ Ready in Xs
```

## 🐳 Build từng service riêng (Debug)

Nếu vẫn lỗi, build từng cái một:

```bash
# 1. Build và chạy chỉ PostgreSQL + Redis
docker compose up -d postgres redis
docker compose ps  # Check status

# 2. Build backend
docker compose build backend
docker compose up -d backend
docker compose logs -f backend  # Watch for errors

# 3. Build frontend
docker compose build frontend
docker compose up -d frontend
docker compose logs -f frontend

# 4. Start workers
docker compose up -d worker beat

# 5. Start Superset
docker compose up -d superset
```

## 💡 Lỗi thường gặp sau khi rebuild

### Lỗi 1: "Cannot connect to database"
```bash
# PostgreSQL chưa ready
docker compose logs postgres | grep "ready"

# Đợi thêm 10-20 giây rồi restart backend
docker compose restart backend
```

### Lỗi 2: "Port already allocated"
```bash
# Port bị chiếm
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Hoặc đổi port trong docker-compose.yml
ports:
  - "8001:8000"  # Đổi thành 8001
```

### Lỗi 3: "Module not found" trong backend
```bash
# Rebuild backend với no cache
docker compose build --no-cache backend
docker compose up -d backend
docker compose logs -f backend
```

### Lỗi 4: Frontend không load được
```bash
# Xóa node_modules trong container
docker compose run --rm frontend rm -rf node_modules
docker compose build frontend
docker compose up -d frontend
```

## 📊 Resource Monitoring

Xem resource usage:
```bash
docker stats
```

Expected usage:
- PostgreSQL: ~200-300MB RAM
- Redis: ~10-20MB RAM
- Backend: ~150-250MB RAM
- Frontend: ~300-500MB RAM
- Worker: ~100-150MB RAM
- Beat: ~50-100MB RAM
- Superset: ~500-800MB RAM

**Total:** ~1.5-2GB RAM

## ✅ Checklist thành công

Sau khi `docker compose up`, kiểm tra:

- [ ] `docker compose ps` shows all services "Up"
- [ ] http://localhost:3000 loads (Frontend)
- [ ] http://localhost:8000/docs loads (Backend API)
- [ ] http://localhost:8088 loads (Superset)
- [ ] `docker compose logs backend` shows "Application startup complete"
- [ ] `docker compose logs frontend` shows "Ready in Xs"
- [ ] Login được với user@test.com / user123
- [ ] API endpoint works: curl http://localhost:8000/api/v1/jobs

## 🆘 Vẫn không được?

### Option 1: Chạy local thay vì Docker
```bash
# Terminal 1 - Backend
cd backend
pip install fastapi uvicorn python-multipart python-docx PyMuPDF celery redis httpx
python run.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Option 2: Reset hoàn toàn Docker
```bash
# Dừng và xóa TẤT CẢ
docker compose down -v
docker system prune -a --volumes

# Build lại từ đầu
docker compose build --no-cache
docker compose up
```

### Option 3: Debug từng container
```bash
# Vào shell của backend container
docker compose exec backend bash

# Trong container, test manual
cd /app
python -c "from app.main import app; print('Import OK')"
pip list  # Check installed packages
```

## 📞 Contact

Nếu vẫn lỗi sau khi thử tất cả, gửi logs:
```bash
docker compose logs > logs.txt
```

Gửi file logs.txt kèm mô tả lỗi.

---

**Last updated:** 2026-10-22  
**Status:** Fixed requirements.txt & Dockerfile
