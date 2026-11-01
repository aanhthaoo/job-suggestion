# 🚀 Chạy nhanh JobPortal - One Command

## Cách 1: Docker (Khuyến nghị - Đầy đủ nhất)

```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose up
```

**Đợi 3-5 phút build lần đầu**, sau đó truy cập:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Superset: http://localhost:8088

**Tài khoản demo:**
- User: `user@test.com` / `user123`
- Admin: `admin@test.com` / `admin123`

---

## Cách 2: Chạy local (Nhanh hơn cho dev)

### Terminal 1 - Backend:
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion\backend"
pip install fastapi uvicorn python-multipart python-docx PyMuPDF celery redis httpx
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 - Frontend:
```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion\frontend"
npm run dev
```

Truy cập:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

---

## Kiểm tra nhanh

✅ **Frontend hoạt động:** Mở http://localhost:3000 → Thấy trang chủ  
✅ **Backend hoạt động:** Mở http://localhost:8000/docs → Thấy Swagger UI  
✅ **Login được:** user@test.com / user123  
✅ **Xem jobs:** http://localhost:3000/jobs  
✅ **Recommendations:** http://localhost:3000/recommendations (sau khi login)  
✅ **Admin dashboard:** http://localhost:3000/admin/dashboard (với admin account)  

---

## Dừng hệ thống

### Docker:
```bash
docker compose down        # Tạm dừng (giữ data)
docker compose down -v     # Reset hoàn toàn (xóa data)
```

### Local:
```
Ctrl+C trong mỗi terminal
```

---

## Xem logs (Docker)

```bash
docker compose logs -f          # Tất cả services
docker compose logs -f frontend # Chỉ frontend
docker compose logs -f backend  # Chỉ backend
docker compose logs -f worker   # Celery worker
```

---

## Tài liệu chi tiết

- **DOCKER_SETUP.md** - Hướng dẫn Docker chi tiết
- **GETTING_STARTED.md** - Hướng dẫn chạy local chi tiết
- **PROJECT_SUMMARY.md** - Tổng kết dự án
- **IMPLEMENTATION_PLAN.md** - Kế hoạch 12 tuần

---

**Sẵn sàng demo!** 🎓
