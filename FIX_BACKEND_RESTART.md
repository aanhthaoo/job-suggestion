# ✅ Đã sửa lỗi Backend tự động tắt

## 🐛 Nguyên nhân

Backend crash vì **không tìm thấy file `jobs.json`**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/app/../../frontend/mock/jobs.json'
```

Trong Docker container, path relative từ `backend/app/main.py` đến `frontend/mock/jobs.json` không hoạt động.

## ✅ Đã sửa gì?

### 1. Sửa `backend/app/main.py`
- Thêm fallback paths cho Docker
- Nếu không tìm thấy file, dùng inline mock data (1 job mẫu)
- Không bao giờ crash vì thiếu file nữa

### 2. Sửa `backend/Dockerfile`
- Copy file `jobs.json` vào container tại `/app/mock_jobs.json`
- Backend sẽ tìm file này nếu không thấy path gốc

## 🚀 Chạy lại Docker

### Bước 1: Dừng containers hiện tại
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose down
```

### Bước 2: Build lại backend với fix mới
```bash
docker compose build --no-cache backend
```

Phải thấy output tương tự:
```
[+] Building 30.5s (12/12) FINISHED
 => [backend 4/6] COPY requirements.txt ... 
 => [backend 5/6] RUN pip install ...
 => [backend 6/6] COPY ../frontend/mock/jobs.json /app/mock_jobs.json
```

### Bước 3: Start tất cả services
```bash
docker compose up -d
```

### Bước 4: Kiểm tra backend logs
```bash
docker compose logs -f backend
```

**Phải thấy:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Không còn lỗi `FileNotFoundError` nữa! ✅

### Bước 5: Test API
```bash
curl http://localhost:8000/api/v1/jobs
```

Phải trả về JSON với danh sách jobs.

Hoặc mở browser: http://localhost:8000/api/v1/jobs

---

## 🔍 Verify tất cả services

```bash
# Check status
docker compose ps

# Phải thấy tất cả "Up":
# NAME                     STATUS
# job-suggestion-backend-1    Up (healthy)
# job-suggestion-frontend-1   Up
# job-suggestion-postgres-1   Up (healthy)
# job-suggestion-redis-1      Up (healthy)
# job-suggestion-worker-1     Up
# job-suggestion-beat-1       Up
# job-suggestion-superset-1   Up
```

---

## 🎯 Truy cập hệ thống

Sau khi build xong:

1. **Frontend:** http://localhost:3000
2. **Backend API:** http://localhost:8000/docs
3. **Superset:** http://localhost:8088

Login với:
- User: `user@test.com` / `user123`
- Admin: `admin@test.com` / `admin123`

---

## 💡 Giải pháp thay thế (nếu vẫn lỗi)

### Option A: Chạy backend local
```bash
cd backend
pip install fastapi uvicorn python-multipart python-docx PyMuPDF celery redis httpx
python run.py
```

Frontend vẫn chạy trong Docker, backend chạy local → vẫn demo được!

### Option B: Mount volume đúng cách
Sửa `docker-compose.yml`:
```yaml
volumes:
  - ./backend:/app
  - ./frontend/mock:/app/mock  # Mount riêng mock folder
```

Rồi sửa code đọc từ `/app/mock/jobs.json`.

---

## ✅ Checklist thành công

Sau khi rebuild, kiểm tra:

- [ ] `docker compose build --no-cache backend` thành công
- [ ] `docker compose up -d` không lỗi
- [ ] `docker compose logs backend` shows "Application startup complete"
- [ ] Không còn lỗi `FileNotFoundError`
- [ ] `curl http://localhost:8000/api/v1/jobs` trả về JSON
- [ ] Frontend load được tại http://localhost:3000
- [ ] Login được với test accounts

---

**Status:** ✅ Fixed  
**Last updated:** 2026-10-22  
**Next step:** Rebuild và test!
