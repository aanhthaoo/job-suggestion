# Backend Setup & Troubleshooting

## 🚀 Cách chạy Backend

### Option 1: Dùng run.py (Khuyến nghị - Đơn giản nhất)

```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion\backend"

# Cài đặt dependencies (chỉ lần đầu)
pip install fastapi uvicorn python-multipart python-docx PyMuPDF celery redis httpx pydantic-settings

# Chạy server
python run.py
```

Server sẽ chạy tại: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

---

### Option 2: Dùng uvicorn trực tiếp

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Option 3: Docker (Tự động với toàn bộ stack)

```bash
cd "D:\individual\tlu document\business intelligence system\btap5-job\job-suggestion"
docker compose up backend
```

---

## 📦 Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-multipart` - File upload support

### Smart Features
- `python-docx` - DOCX file parsing
- `PyMuPDF` - PDF file parsing (fitz)
- `celery` - Background tasks
- `redis` - Message broker

### HTTP Client
- `httpx` - Async HTTP client for API calls

### Install all:
```bash
pip install -r requirements.txt
```

Hoặc cài từng cái:
```bash
pip install fastapi uvicorn python-multipart python-docx PyMuPDF celery redis httpx pydantic-settings
```

---

## 🐛 Lỗi thường gặp & Cách sửa

### 1. ModuleNotFoundError: No module named 'fastapi'

**Nguyên nhân:** Chưa cài dependencies

**Giải pháp:**
```bash
pip install fastapi uvicorn python-multipart
```

---

### 2. ImportError: cannot import name 'X' from 'app.matching'

**Nguyên nhân:** Relative imports không hoạt động khi chạy `python -m app.main`

**Giải pháp:** Dùng `python run.py` thay vì `python -m app.main`

Hoặc dùng uvicorn:
```bash
uvicorn app.main:app --reload
```

---

### 3. FileNotFoundError: skill_alias.csv not found

**Nguyên nhân:** File skill_alias.csv không tồn tại trong thư mục data/

**Giải pháp:**
File đã có tại: `../data/skill_alias.csv`

Kiểm tra:
```bash
ls ../data/skill_alias.csv
```

Nếu không có, code sẽ dùng default aliases (70+ skills).

---

### 4. PyMuPDF installation failed

**Trên Windows:**
```bash
pip install PyMuPDF
```

Nếu lỗi, tải wheel từ: https://pypi.org/project/PyMuPDF/#files

**Trên Linux/Mac:**
```bash
pip install PyMuPDF
```

---

### 5. Port 8000 already in use

**Kiểm tra process:**
```bash
netstat -ano | findstr :8000
```

**Kill process:**
```bash
taskkill /PID <PID> /F
```

**Hoặc đổi port:**
```bash
uvicorn app.main:app --reload --port 8001
```

---

### 6. CORS error khi frontend gọi API

Đã được cấu hình trong `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Nếu vẫn lỗi, thêm origin của bạn vào list.

---

## ✅ Kiểm tra Backend hoạt động

### 1. Mở trang chủ API
```
http://localhost:8000
```
Phải thấy: `{"detail":"Not Found"}` (bình thường, vì root endpoint chưa có)

### 2. Mở API Docs
```
http://localhost:8000/docs
```
Phải thấy Swagger UI với danh sách endpoints

### 3. Test endpoint đơn giản
```
http://localhost:8000/api/v1/jobs
```
Phải trả về JSON với danh sách jobs

### 4. Test login
Trong Swagger UI:
- Tìm POST `/api/v1/auth/login`
- Click "Try it out"
- Enter:
  ```json
  {
    "email": "user@test.com",
    "password": "user123"
  }
  ```
- Click "Execute"
- Phải nhận được access_token

---

## 📁 Cấu trúc Backend

```
backend/
├── app/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI application (300+ lines)
│   ├── matching.py           # Auto-matching algorithm
│   ├── cv_parser.py          # CV parsing service
│   ├── tasks.py              # Celery background tasks
│   └── celery_app.py         # Celery configuration
├── uploads/                  # Temporary CV uploads (auto-created)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Backend container
├── run.py                    # Standalone runner (recommended)
└── README.md                 # This file
```

---

## 🔧 Environment Variables

Tạo file `.env` trong thư mục backend (optional):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobportal
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

Hiện tại code dùng mock data nên không cần database thật.

---

## 🎯 Endpoints chính

### Public
- `GET /api/v1/jobs` - List jobs with filters
- `GET /api/v1/jobs/{id}` - Job detail
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register

### Protected (cần JWT token)
- `GET /api/v1/users/me` - Current user info
- `POST /api/v1/applications` - Apply to job
- `GET /api/v1/applications` - User's applications
- `POST /api/v1/saved-jobs` - Save job
- `GET /api/v1/saved-jobs` - List saved jobs

### Smart Features
- `POST /api/v1/match/calculate` - Calculate match score
- `GET /api/v1/recommendations` - Get personalized recommendations
- `POST /api/v1/cv/parse` - Parse uploaded CV

### Admin
- `GET /api/v1/admin/stats` - System health stats
- `GET /api/v1/admin/tasks` - Background tasks list
- `POST /api/v1/admin/tasks/sync-now` - Trigger manual sync

---

## 💡 Tips

### Hot reload
Uvicorn tự động reload khi code thay đổi:
```bash
uvicorn app.main:app --reload
```

### Debug mode
Thêm log statements:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get("/test")
def test():
    logger.debug("This is a debug message")
    return {"message": "OK"}
```

### Performance testing
Install wrk hoặc ab:
```bash
ab -n 1000 -c 10 http://localhost:8000/api/v1/jobs
```

---

**Liên hệ:** support@jobportal.vn  
**Last updated:** 2026-10-22
