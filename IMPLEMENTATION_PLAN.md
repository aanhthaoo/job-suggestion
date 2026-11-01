# Kế Hoạch Triển Khai Hệ Thống Tìm Việc Làm Thông Minh (AI-Driven Job Portal)

**Mục tiêu:** Xây dựng bản demo vận hành được trong Docker với giao diện hoàn chỉnh, sau đó mở rộng các tính năng thông minh và quy trình xử lý dữ liệu.

**Nguyên tắc:** 
- Tất cả công nghệ phải **miễn phí** và **triển khai đơn giản**
- Ưu tiên giao diện trước → tính năng cơ bản → tính năng thông minh → xử lý dữ liệu
- Đóng gói trong Docker Compose (4-5 containers, ~4.5GB RAM)

---

## PHASE 1: GIAO DIỆN HOÀN CHỈNH (Tuần 1-2)

### Mục tiêu
Xây dựng frontend hoàn chỉnh có thể chạy độc lập với mock data, đáp ứng 5 tính năng cơ bản:
1. Quản lý tài khoản & hồ sơ (đăng ký/đăng nhập, upload CV)
2. Tìm kiếm & bộ lọc tiêu chuẩn (từ khóa, địa điểm, lương, ngành nghề)
3. Hiển thị danh sách việc làm (card layout với thông tin cơ bản)
4. Trang chi tiết việc làm (JD đầy đủ, nút ứng tuyển)
5. Dashboard ứng viên (theo dõi trạng thái ứng tuyển, việc làm đã lưu)

### Công nghệ đề xuất
- **Framework:** Next.js 14 (App Router) + TypeScript
  - Lý do: SEO tốt, routing đơn giản, built-in API routes cho phase sau
- **UI Library:** shadcn/ui + Tailwind CSS
  - Lý do: Component sẵn, dễ customize, miễn phí 100%
- **State Management:** Zustand (nhẹ hơn Redux)
- **Form Handling:** React Hook Form + Zod validation
- **HTTP Client:** TanStack Query (React Query)
- **File Upload:** react-dropzone

### Cấu trúc trang
```
/ (trang chủ - tìm kiếm nhanh)
/auth/login
/auth/register
/jobs (danh sách việc làm + bộ lọc sidebar)
/jobs/[id] (chi tiết việc làm)
/profile (quản lý hồ sơ cá nhân)
/profile/cv (upload & quản lý CV)
/applications (theo dõi đơn ứng tuyển)
/saved (việc làm đã lưu)
/company/[id] (trang công ty)
```

### Mock Data Strategy
- Tạo file `mock/jobs.json` với 50-100 tin mẫu từ VietJobs dataset
- Tạo file `mock/companies.json` với 20 công ty mẫu
- Tạo file `mock/users.json` với 5 user mẫu (các vai trò khác nhau)
- Sử dụng MSW (Mock Service Worker) để intercept API calls

### Deliverables Phase 1
- [ ] Project Next.js khởi tạo với TypeScript + Tailwind
- [ ] Cài đặt shadcn/ui components cần thiết (Button, Input, Card, Dialog, Table, etc.)
- [ ] Authentication UI (login/register forms)
- [ ] Layout chính (Header với navigation, Footer)
- [ ] Trang chủ với search bar prominent
- [ ] Trang danh sách việc làm với filters sidebar
- [ ] Job card component (title, company, location, salary, posted date)
- [ ] Trang chi tiết việc làm (full JD, apply button, save button)
- [ ] Profile page với CV upload zone
- [ ] Applications tracking page (table view với status badges)
- [ ] Saved jobs page
- [ ] Responsive design (mobile-first)
- [ ] Dockerfile cho frontend
- [ ] Documentation: README.md hướng dẫn chạy local

### Thời gian ước tính: 7-10 ngày làm việc

---

## PHASE 2: TÍNH NĂNG CƠ BẢN - BACKEND API (Tuần 3-4)

### Mục tiêu
Xây dựng backend API hoàn chỉnh kết nối PostgreSQL, triển khai 5 tính năng cơ bản.

### Công nghệ đề xuất
- **Backend Framework:** FastAPI (Python 3.11)
  - Lý do: Tự động sinh OpenAPI docs, async native, nhẹ, type-safe
- **Database:** PostgreSQL 16 + pgvector extension
  - Lý do: All-in-one (quan hệ + full-text search + vector), miễn phí
- **ORM:** SQLAlchemy 2.0 + Alembic (migrations)
- **Authentication:** JWT (PyJWT) + bcrypt
- **File Storage:** Local filesystem (dev) / MinIO (prod, optional)
- **Background Tasks:** Celery + Redis (cho email notifications)
- **Email:** SMTP (Gmail free tier cho dev)

### API Endpoints cần xây dựng

#### Authentication & Users
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh-token
GET    /api/v1/users/me
PUT    /api/v1/users/me
POST   /api/v1/users/me/cv/upload
GET    /api/v1/users/me/cvs
```

#### Jobs
```
GET    /api/v1/jobs (search + filter + pagination)
GET    /api/v1/jobs/{job_id}
POST   /api/v1/jobs (HR only)
PUT    /api/v1/jobs/{job_id} (HR only)
DELETE /api/v1/jobs/{job_id} (HR only)
```

#### Applications
```
POST   /api/v1/applications (apply to job)
GET    /api/v1/applications (candidate's applications)
GET    /api/v1/applications/{app_id}
PUT    /api/v1/applications/{app_id}/status (HR only)
```

#### Saved Jobs
```
POST   /api/v1/saved-jobs
GET    /api/v1/saved-jobs
DELETE /api/v1/saved-jobs/{job_id}
```

#### Companies
```
GET    /api/v1/companies
GET    /api/v1/companies/{company_id}
POST   /api/v1/companies (HR only)
```

### Database Schema (Core Tables)

```sql
-- users
id (UUID, PK)
email (VARCHAR, UNIQUE)
password_hash (VARCHAR)
full_name (VARCHAR)
phone (VARCHAR)
role (ENUM: candidate, hr, admin)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)

-- cvs
id (UUID, PK)
user_id (UUID, FK -> users.id)
file_path (VARCHAR)
file_name (VARCHAR)
parsed_data (JSONB) -- skills, experience, education extracted
created_at (TIMESTAMP)

-- companies
id (UUID, PK)
name (VARCHAR)
description (TEXT)
logo_path (VARCHAR)
website (VARCHAR)
industry (VARCHAR)
size (ENUM: small, medium, large)
created_at (TIMESTAMP)

-- jobs
id (UUID, PK)
company_id (UUID, FK -> companies.id)
title (VARCHAR)
description (TEXT)
requirements (TEXT)
skills_required (TEXT[]) -- array of skills
location (VARCHAR)
salary_min (DECIMAL)
salary_max (DECIMAL)
currency (VARCHAR, default 'VND')
experience_years (INTEGER)
job_type (ENUM: fulltime, parttime, internship)
work_mode (ENUM: onsite, remote, hybrid)
status (ENUM: active, closed, draft)
posted_at (TIMESTAMP)
expires_at (TIMESTAMP)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)

-- applications
id (UUID, PK)
job_id (UUID, FK -> jobs.id)
user_id (UUID, FK -> users.id)
cv_id (UUID, FK -> cvs.id)
cover_letter (TEXT)
status (ENUM: submitted, reviewed, interviewing, accepted, rejected)
applied_at (TIMESTAMP)
updated_at (TIMESTAMP)

-- saved_jobs
id (UUID, PK)
user_id (UUID, FK -> users.id)
job_id (UUID, FK -> jobs.id)
saved_at (TIMESTAMP)
UNIQUE(user_id, job_id)
```

### Full-Text Search Implementation
Sử dụng PostgreSQL native FTS với `tsvector`:

```python
# Migration thêm full-text search
ALTER TABLE jobs ADD COLUMN search_vector tsvector;
CREATE INDEX idx_jobs_search ON jobs USING GIN(search_vector);

# Trigger tự động update
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
ON jobs FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.simple', title, description);

# Query
SELECT * FROM jobs
WHERE search_vector @@ websearch_to_tsquery('simple', 'python developer');
```

### Admin Dashboard (cho người quản trị hệ thống)

**Mục đích:** Giám sát hoạt động background tasks và chất lượng dữ liệu mà không cần xem logs terminal.

**Trang admin routes:**
```
/admin/dashboard (tổng quan hệ thống)
/admin/tasks (background tasks monitoring)
/admin/data-sources (quản lý nguồn dữ liệu)
/admin/jobs (kiểm duyệt tin đăng)
/admin/users (quản lý người dùng)
```

**Chức năng chi tiết:**

#### 1. Dashboard Overview (`/admin/dashboard`)
- **System health cards:**
  - PostgreSQL status (connected/disconnected, size)
  - Redis status (connected/disconnected, memory usage)
  - Celery worker status (active/idle, số workers)
  - Total jobs count (active/closed)
  - Total users count
  - Today's applications count

- **Quick stats charts:**
  - Jobs added last 7 days (line chart)
  - Applications by status (pie chart)
  - Top 5 companies by job count (bar chart)

#### 2. Background Tasks Monitor (`/admin/tasks`)
- **Table view của recent tasks:**
  ```
  | Task Name              | Status    | Started At         | Duration | Result |
  |------------------------|-----------|--------------------|----------|--------|
  | ingest_greenhouse_jobs | Succeeded | 2026-10-22 12:00   | 45s      | +23 jobs |
  | parse_cv               | Failed    | 2026-10-22 11:30   | 2s       | Error: invalid PDF |
  | reconcile_jobs         | Running   | 2026-10-22 13:00   | 12s      | -      |
  ```

- **Filter by status:** All / Success / Failed / Running
- **Retry button** cho failed tasks
- **Force trigger button** để chạy manual (ví dụ: "Sync Now")

#### 3. Data Sources Management (`/admin/data-sources`)
- **List các nguồn dữ liệu đã cấu hình:**
  ```
  | Source      | Type     | Last Sync          | Jobs Imported | Status  | Actions      |
  |-------------|----------|--------------------|---------------|---------|--------------|
  | VietJobs    | Kaggle   | 2026-10-20 10:00   | 48,092        | Done    | [Re-import]  |
  | Greenhouse  | API      | 2026-10-22 12:00   | 156           | Active  | [Sync Now]   |
  | Lever       | API      | Never              | 0             | Inactive| [Configure]  |
  ```

- **Add new source form:**
  - Source type dropdown (Greenhouse/Lever/Ashby/Manual)
  - Token/API key input
  - Board name/company identifier
  - Test connection button

- **Toggle scheduled sync:** Bật/tắt automatic ingestion cho từng source

#### 4. Jobs Moderation (`/admin/jobs`)
- **Table view với filters:**
  - Filter by status: All / Active / Closed / Draft / Flagged
  - Filter by source: API / HR-posted / Kaggle
  - Search by title/company

- **Actions cho mỗi job:**
  - View detail (preview JD)
  - Edit job (sửa thông tin nếu sai)
  - Delete job (xóa spam/duplicate)
  - Flag job (đánh dấu để review sau)

- **Bulk actions:**
  - Select multiple → Close all
  - Select multiple → Delete all

#### 5. User Management (`/admin/users`)
- **Users table:**
  ```
  | Email           | Role      | Joined             | CVs Uploaded | Applications | Actions    |
  |-----------------|-----------|--------------------|--------------|--------------|------------|
  | user@test.com   | Candidate | 2026-10-15         | 2            | 5            | [View]     |
  | hr@company.com  | HR        | 2026-10-10         | 0            | 0            | [View]     |
  ```

- **Admin actions:**
  - Change user role (Candidate ↔ HR ↔ Admin)
  - Deactivate user (ban spammer)
  - View user detail (xem profile, CVs, applications)

### Tech Stack cho Admin UI
- **Reuse cùng Next.js app** với user-facing frontend
- **Protected route:** `/admin/*` chỉ accessible bởi users có `role = 'admin'`
- **Middleware check:**
  ```typescript
  // middleware.ts
  if (pathname.startsWith('/admin')) {
    const user = await getCurrentUser();
    if (user?.role !== 'admin') {
      return NextResponse.redirect('/auth/login');
    }
  }
  ```
- **Components:** Reuse shadcn/ui components (Table, Card, Button, Dialog)
- **Charts:** Recharts hoặc Chart.js (lightweight, dễ tích hợp)

### Backend APIs cho Admin
```python
# Admin-only endpoints
GET    /api/v1/admin/stats              # System health & quick stats
GET    /api/v1/admin/tasks              # List background tasks
POST   /api/v1/admin/tasks/{task_id}/retry  # Retry failed task
POST   /api/v1/admin/tasks/sync-now     # Trigger manual sync
GET    /api/v1/admin/data-sources       # List configured sources
POST   /api/v1/admin/data-sources       # Add new source
PUT    /api/v1/admin/data-sources/{id}  # Update source config
DELETE /api/v1/admin/data-sources/{id}  # Remove source
GET    /api/v1/admin/jobs               # List jobs with filters
PUT    /api/v1/admin/jobs/{id}          # Edit job
DELETE /api/v1/admin/jobs/{id}         # Delete job
GET    /api/v1/admin/users              # List users
PUT    /api/v1/admin/users/{id}/role    # Change user role
```

### Deliverables Phase 2 (Updated)
- [ ] Docker Compose với PostgreSQL + Redis + FastAPI
- [ ] Database migrations với Alembic
- [ ] Authentication system (register, login, JWT)
- [ ] CRUD APIs cho Users, Companies, Jobs
- [ ] Application workflow API
- [ ] Saved jobs API
- [ ] Full-text search với PostgreSQL
- [ ] File upload handler (CV PDF/DOCX)
- [ ] Background task setup (Celery + Redis)
- [ ] Email notification service
- [ ] **Admin dashboard pages (/admin/*)**
- [ ] **Admin monitoring APIs**
- [ ] **Role-based access control (admin vs user vs hr)**
- [ ] API documentation (Swagger UI auto-generated)
- [ ] Integration tests (pytest)
- [ ] Frontend integrate với backend API
- [ ] Dockerfile cho backend

### Thời gian ước tính: 12-16 ngày làm việc (thêm 2 ngày cho admin UI)

---

## PHASE 3: TÍNH NĂNG THÔNG MINH - MVP (Tuần 5-7)

### Mục tiêu
Triển khai 3 tính năng thông minh cốt lõi với cách tiếp cận đơn giản nhất:
1. **Smart CV Parsing** (OCR + rule-based extraction)
2. **Auto-Matching & Scoring** (skill overlap + cosine similarity)
3. **Personalized Recommendations** (content-based filtering)

### Công nghệ đề xuất

#### 3.1 Smart CV Parsing
- **PDF Extraction:** PyMuPDF (fitz) - nhẹ, nhanh, miễn phí
- **DOCX Extraction:** python-docx
- **OCR (nếu cần):** pytesseract + Tesseract OCR (install qua apt)
- **NER (Named Entity Recognition):** spaCy với model `en_core_web_sm` hoặc `vi_core_news_lg`
- **Skill Extraction:** Rule-based + keyword matching với skill taxonomy CSV

**Pipeline:**
```
CV File → Extract text → Clean (remove HTML, normalize Unicode) → 
NER extract (skills, experience, education) → Match with skill_alias.csv → 
Store parsed_data as JSONB in cvs table
```

**Skill Alias Mapping:**
Tạo file `data/skill_alias.csv`:
```csv
canonical,aliases
Python,"python,py,python programming"
JavaScript,"javascript,js,ecmascript"
React,"react,reactjs,react.js"
PostgreSQL,"postgresql,postgres,psql"
Machine Learning,"machine learning,ml,deep learning,dl"
```

#### 3.2 Auto-Matching & Scoring
**Thuật toán đơn giản (không cần ML phức tạp):**

```python
def calculate_match_score(cv_parsed: dict, job: dict) -> float:
    """
    Score = 0.40 * skill_overlap + 0.35 * experience_fit + 0.25 * other_factors
    
    skill_overlap: Jaccard similarity giữa cv_skills và job_skills
    experience_fit: min(cv_exp / job_exp_required, 1.0)
    other_factors: location match, work mode preference, etc.
    """
    # 1. Skill overlap (Jaccard)
    cv_skills = set(cv_parsed.get('skills', []))
    job_skills = set(job.get('skills_required', []))
    
    if not job_skills:
        skill_score = 0.5
    else:
        intersection = cv_skills.intersection(job_skills)
        union = cv_skills.union(job_skills)
        skill_score = len(intersection) / len(union) if union else 0
    
    # 2. Experience fit
    cv_exp = cv_parsed.get('experience_years', 0)
    job_exp_req = job.get('experience_years', 0)
    exp_score = min(cv_exp / job_exp_req, 1.0) if job_exp_req > 0 else 1.0
    
    # 3. Other factors (location, work mode)
    location_score = 1.0 if cv_parsed.get('location') == job.get('location') else 0.5
    
    # Weighted sum
    total_score = (0.40 * skill_score) + (0.35 * exp_score) + (0.25 * location_score)
    
    return round(total_score, 2)

def generate_match_reason(cv_parsed: dict, job: dict, score: float) -> dict:
    """Tạo giải thích tại sao match score như vậy"""
    cv_skills = set(cv_parsed.get('skills', []))
    job_skills = set(job.get('skills_required', []))
    
    matched_skills = list(cv_skills.intersection(job_skills))
    missing_skills = list(job_skills - cv_skills)
    
    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience_gap": max(0, job.get('experience_years', 0) - cv_parsed.get('experience_years', 0)),
        "recommendation": "Rất phù hợp" if score >= 0.7 else "Phù hợp" if score >= 0.5 else "Cân nhắc"
    }
```

**Threshold hiển thị:**
- Score ≥ 0.70: "Rất phù hợp" (badge xanh lá)
- Score ≥ 0.55: "Phù hợp" (badge xanh dương)
- Score < 0.55: Ẩn hoặc hiển thị cuối danh sách

#### 3.3 Personalized Recommendations (Content-Based)
**Cách tiếp cận đơn giản (không cần collaborative filtering):**

1. **Build user profile từ lịch sử:**
   - Skills từ CV đã upload
   - Jobs đã apply (extract skills từ những job này)
   - Jobs đã save (extract skills)
   - Search history keywords

2. **Recommendation algorithm:**
```python
def recommend_jobs(user_id: str, top_k: int = 10) -> List[dict]:
    """
    Recommend jobs dựa trên user profile
    """
    # 1. Get user profile
    user_cvs = get_user_cvs(user_id)
    applied_jobs = get_user_applications(user_id)
    saved_jobs = get_user_saved_jobs(user_id)
    
    # 2. Aggregate skills from all sources
    user_skills = set()
    for cv in user_cvs:
        user_skills.update(cv.parsed_data.get('skills', []))
    
    for app in applied_jobs:
        user_skills.update(app.job.skills_required)
    
    for saved in saved_jobs:
        user_skills.update(saved.job.skills_required)
    
    # 3. Find jobs matching these skills (exclude already applied)
    recommended = db.query(Job).filter(
        Job.status == 'active',
        Job.id.notin_([app.job_id for app in applied_jobs])
    ).order_by(
        # Sort by number of matching skills descending
        func.array_length(func.array_intersect(Job.skills_required, list(user_skills)), 1).desc()
    ).limit(top_k * 2).all()
    
    # 4. Calculate match score for each
    scored_jobs = []
    for job in recommended:
        score = calculate_match_score({"skills": list(user_skills)}, job)
        if score >= 0.55:  # threshold
            scored_jobs.append((job, score))
    
    # 5. Sort by score and return top_k
    scored_jobs.sort(key=lambda x: x[1], reverse=True)
    return [(job, score) for job, score in scored_jobs[:top_k]]
```

### Vector Embeddings (Optional - Phase 3 nâng cao)
Nếu muốn semantic search tốt hơn:

- **Model:** `intfloat/multilingual-e5-small` (384 dims, hỗ trợ tiếng Việt)
- **Storage:** pgvector extension trong PostgreSQL
- **Usage:** Store embeddings của job descriptions và CV text

```python
# Migration thêm vector column
from pgvector.sqlalchemy import Vector

class Job(Base):
    __tablename__ = 'jobs'
    
    description_embedding = mapped_column(Vector(384))

# Generate embedding
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('intfloat/multilingual-e5-small')

job.embedding = model.encode(f"document: {job.description}")

# Similarity search
from sqlalchemy import func

similar_jobs = db.query(Job).order_by(
    Job.description_embedding.cosine_distance(query_embedding)
).limit(10).all()
```

**Lưu ý:** Chỉ thêm nếu Phase 3 cơ bản xong sớm. Đây là nice-to-have, không bắt buộc.

### Deliverables Phase 3
- [ ] CV parsing service (PDF + DOCX extraction)
- [ ] Skill extraction với rule-based + alias mapping
- [ ] Auto-matching scoring API endpoint
- [ ] Match reason generation (giải thích tại sao score như vậy)
- [ ] Personalized recommendations API
- [ ] Frontend: Hiển thị match score badge trên job cards
- [ ] Frontend: Trang "Việc làm gợi ý cho bạn"
- [ ] Frontend: Skill gap analysis (hiển thị kỹ năng còn thiếu)
- [ ] Unit tests cho matching algorithms
- [ ] Documentation: Giải thích thuật toán scoring

### Thời gian ước tính: 14-21 ngày làm việc

---

## PHASE 4: XỬ LÝ DỮ LIỆU & INTEGRATION (Tuần 8-10)

### Mục tiêu
Xây dựng data pipeline thu thập dữ liệu từ nguồn bên ngoài, làm sạch và đưa vào database.

### 4.1 Data Sources

#### A. Analytical Snapshot (dữ liệu tĩnh, load 1 lần)
1. **VietJobs Dataset (Kaggle)**
   - Link: https://www.kaggle.com/datasets/thanhledev/vietjobs48k
   - 48,092 tin tuyển dụng
   - License: CC BY 4.0
   - Xử lý: Load vào database một lần, không update

2. **ESCO Skills Taxonomy**
   - Link: https://esco.ec.europa.eu/en/classification/skills
   - Download CSV với ~13,000 skills
   - Dùng để chuẩn hóa skill names

3. **O*NET Occupational Data**
   - Link: https://www.onetcenter.org/database.html
   - Thông tin về nghề nghiệp, kỹ năng yêu cầu

#### B. Live Data (cập nhật định kỳ mỗi 12h)
1. **Greenhouse Job Board API**
   ```
   GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs
   
   Tokens đã verify hoạt động:
   - navervietnam
   - (tìm thêm từ site:job-boards.greenhouse.io vietnam)
   ```

2. **Lever Job Board API**
   ```
   GET https://api.lever.co/v0/postings/{token}?mode=json
   ```

3. **Ashby Job Board API**
   ```
   GET https://api.ashbyhq.com/posting-api/job-board/{token}
   ```

4. **HR đăng trực tiếp** (qua form trong hệ thống)

### 4.2 Data Pipeline Architecture

```
┌─────────────────────┐
│  Data Sources       │
│  (Kaggle/APIs/HR)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Ingestion Worker   │
│  (Celery Beat)      │
│  - Batch: 12h/lần  │
│  - Real-time: HR    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ETL Processor      │
│  (Python scripts)   │
│  1. Raw storage     │
│  2. Normalize       │
│  3. Deduplicate     │
│  4. Skill mapping   │
│  5. Salary standard │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PostgreSQL         │
│  (jobs table)       │
│  - FTS index        │
│  - Vector index     │
└─────────────────────┘
```

### 4.3 ETL Steps Chi Tiết

#### Step 1: Lưu bản gốc (Raw Storage)
```python
# Bảng raw_source để lưu dữ liệu gốc phòng khi cần reprocess
class RawSource(Base):
    __tablename__ = 'raw_sources'
    
    id = Column(UUID, primary_key=True)
    source_type = Column(Enum('kaggle', 'greenhouse', 'lever', 'ashby', 'hr'))
    raw_data = Column(JSONB)  # Toàn bộ response gốc
    ingested_at = Column(DateTime, default=datetime.utcnow)
```

#### Step 2: Chuẩn hóa (Normalization)
```python
import unicodedata
import re

def normalize_text(text: str) -> str:
    """Chuẩn hóa Unicode, bỏ dấu tiếng Việt cho search"""
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text.strip()

def remove_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt cho text_nodiacritic column"""
    nfd = unicodedata.normalize('NFD', text)
    no_combining = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    return no_combining
```

#### Step 3: Khử trùng lặp (Deduplication)
```python
import hashlib

def generate_job_key(title: str, company: str, city: str) -> str:
    """Tạo unique key để phát hiện duplicate"""
    normalized = f"{title.lower().strip()}|{company.lower().strip()}|{city.lower().strip()}"
    return hashlib.md5(normalized.encode()).hexdigest()

# Trong ingestion logic
existing = db.query(Job).filter(
    Job.job_key == new_job_key
).first()

if existing:
    # Update last_seen_at, không tạo mới
    existing.last_seen_at = datetime.utcnow()
else:
    # Insert new job
    new_job = Job(..., job_key=new_job_key, last_seen_at=datetime.utcnow())
    db.add(new_job)
```

#### Step 4: Chuẩn hóa kỹ năng (Skill Mapping)
```python
import csv

# Load skill aliases
skill_aliases = {}
with open('data/skill_alias.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        canonical = row['canonical']
        aliases = row['aliases'].split(',')
        for alias in aliases:
            skill_aliases[alias.strip().lower()] = canonical

def extract_and_map_skills(text: str) -> List[str]:
    """Extract skills từ text và map với canonical names"""
    found_skills = []
    text_lower = text.lower()
    
    for alias, canonical in skill_aliases.items():
        if alias in text_lower:
            found_skills.append(canonical)
    
    return list(set(found_skills))  # unique
```

#### Step 5: Chuẩn hóa lương (Salary Standardization)
```python
def parse_salary(salary_str: str) -> dict:
    """
    Parse các định dạng lương khác nhau về min/max/currency
    
    Examples:
    - "15-20 triệu" → {min: 15000000, max: 20000000, currency: 'VND'}
    - "$1000-$1500" → {min: 1000, max: 1500, currency: 'USD'}
    - "Thương lượng" → {min: None, max: None, is_negotiable: True}
    """
    result = {
        'min': None,
        'max': None,
        'currency': 'VND',
        'is_negotiable': False
    }
    
    if not salary_str or 'thương lượng' in salary_str.lower():
        result['is_negotiable'] = True
        return result
    
    # Extract numbers
    numbers = re.findall(r'[\d,.]+', salary_str)
    if len(numbers) >= 2:
        result['min'] = float(numbers[0].replace(',', ''))
        result['max'] = float(numbers[1].replace(',', ''))
    elif len(numbers) == 1:
        result['min'] = float(numbers[0].replace(',', ''))
        result['max'] = result['min']
    
    # Detect currency
    if '$' in salary_str or 'usd' in salary_str.lower():
        result['currency'] = 'USD'
    elif '€' in salary_str or 'eur' in salary_str.lower():
        result['currency'] = 'EUR'
    
    # Detect unit (triệu/ngàn)
    if 'triệu' in salary_str.lower() or 'million' in salary_str.lower():
        if result['min']:
            result['min'] *= 1_000_000
        if result['max']:
            result['max'] *= 1_000_000
    elif 'nghìn' in salary_str.lower() or 'thousand' in salary_str.lower():
        if result['min']:
            result['min'] *= 1_000
        if result['max']:
            result['max'] *= 1_000
    
    return result
```

#### Step 6: Reconciliation (Đóng tin hết hạn)
```python
# Chạy mỗi 12h sau khi ingest xong
def reconcile_jobs():
    """Đánh dấu jobs không thấy nữa là closed"""
    two_cycles_ago = datetime.utcnow() - timedelta(hours=24)
    
    stale_jobs = db.query(Job).filter(
        Job.source_type.in_(['greenhouse', 'lever', 'ashby']),
        Job.status == 'active',
        Job.last_seen_at < two_cycles_ago
    ).all()
    
    for job in stale_jobs:
        job.status = 'closed'
        job.closed_at = datetime.utcnow()
    
    db.commit()
```

### 4.4 Scheduled Tasks (Celery Beat)

```python
# celeryconfig.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'ingest-greenhouse-jobs': {
        'task': 'tasks.ingest_greenhouse_jobs',
        'schedule': crontab(hour='0,12'),  # Mỗi 12h
    },
    'ingest-lever-jobs': {
        'task': 'tasks.ingest_lever_jobs',
        'schedule': crontab(hour='0,12'),
    },
    'reconcile-jobs': {
        'task': 'tasks.reconcile_jobs',
        'schedule': crontab(minute=30, hour='1,13'),  # Sau ingest 30 phút
    },
    'generate-recommendations': {
        'task': 'tasks.generate_user_recommendations',
        'schedule': crontab(minute=0, hour='2'),  # Mỗi đêm
    },
}
```

### 4.5 Apache Superset Integration (yêu cầu môn học)

**Mục đích:** Hiển thị dashboard analytics cho giảng viên đánh giá

**Setup:**
```yaml
# docker-compose.yml
superset:
  image: apache/superset:latest
  ports:
    - "8088:8088"
  environment:
    - SUPERSET_LOAD_EXAMPLES=no
  volumes:
    - superset_home:/app/superset_home
  depends_on:
    - postgres
```

**Dashboards cần tạo:**
1. **Job Market Overview**
   - Tổng số jobs theo ngành nghề (pie chart)
   - Jobs theo địa điểm (map visualization)
   - Average salary theo vị trí (bar chart)
   - Top 10 skills most in-demand (horizontal bar)

2. **User Activity**
   - Số lượng applications theo thời gian (line chart)
   - Conversion rate (applied/interviewed/accepted)
   - Top companies by applications received

3. **Matching Quality**
   - Distribution of match scores (histogram)
   - Average match score by industry
   - Skills gap analysis (most missing skills)

**Cách kết nối Superset với PostgreSQL:**
1. Vào Superset → Settings → Database Connections
2. Add new database: `postgresql://user:pass@postgres:5432/jobportal`
3. Create datasets từ tables: jobs, applications, users
4. Build charts từ datasets

### Deliverables Phase 4
- [ ] Data ingestion scripts cho Kaggle dataset
- [ ] Greenhouse API integration
- [ ] Lever/Ashby API integration (nếu tìm được tokens)
- [ ] ETL pipeline với 5 steps (normalize, dedup, skill mapping, salary parse, store)
- [ ] Deduplication mechanism với job_key
- [ ] Reconciliation task (đóng tin stale)
- [ ] Celery Beat scheduled tasks
- [ ] Raw source storage (JSONB)
- [ ] Skill alias mapping CSV
- [ ] Apache Superset setup trong Docker
- [ ] 3 Superset dashboards (Job Market, User Activity, Matching Quality)
- [ ] Data quality metrics monitoring
- [ ] Documentation: Hướng dẫn thêm API token mới

### Thời gian ước tính: 14-21 ngày làm việc

---

## PHASE 5: TESTING & DEPLOYMENT (Tuần 11-12)

### 5.1 Testing Strategy

#### Unit Tests
```bash
# Backend
pytest tests/unit/test_matching.py
pytest tests/unit/test_etl.py
pytest tests/unit/test_auth.py

# Frontend
npm test -- src/components/__tests__/
```

#### Integration Tests
```bash
# API endpoints
pytest tests/integration/test_jobs_api.py
pytest tests/integration/test_applications.py

# Database
pytest tests/integration/test_fulltext_search.py
```

#### E2E Tests (Optional)
```bash
# Cypress hoặc Playwright
cypress run --spec "cypress/e2e/apply_job.cy.ts"
```

### 5.2 Performance Metrics Targets
- **Search latency p95:** ≤ 800ms (với 10k jobs trong DB)
- **Match score calculation:** ≤ 100ms per job
- **Recommendation generation:** ≤ 2s per user
- **Concurrent users:** 50+ (test với k6 hoặc locust)

### 5.3 Docker Compose Production Setup

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: jobportal
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/jobportal
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/jobportal
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  beat:
    build: ./backend
    command: celery -A app.celery beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/jobportal
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    depends_on:
      - backend

  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      SUPERSET_LOAD_EXAMPLES: "no"
    volumes:
      - superset_home:/app/superset_home
    depends_on:
      - postgres

volumes:
  postgres_data:
  superset_home:
```

### 5.4 Deployment Checklist
- [ ] Environment variables configured (.env file)
- [ ] Database migrations run successfully
- [ ] All services healthy (`docker compose ps`)
- [ ] API endpoints accessible
- [ ] Frontend loading correctly
- [ ] Background tasks running (check Celery logs)
- [ ] Superset dashboards working
- [ ] SSL certificate (nếu deploy production)
- [ ] Backup strategy (pg_dump cron job)

### Deliverables Phase 5
- [ ] Full test suite (unit + integration)
- [ ] Performance benchmark results
- [ ] Docker Compose production config
- [ ] Deployment documentation
- [ ] Monitoring setup (basic health checks)
- [ ] Backup/restore procedures
- [ ] User manual (tiếng Việt)
- [ ] Technical documentation (architecture, API docs)

### Thời gian ước tính: 7-10 ngày làm việc

---

## TỔNG KÊ THỜI GIAN DỰ KIẾN

| Phase | Nội dung | Thời gian | Tuần hoàn thành |
|-------|----------|-----------|-----------------|
| 1 | Giao diện hoàn chỉnh (mock data) | 7-10 ngày | Tuần 2 |
| 2 | Backend API + Admin dashboard | 12-16 ngày | Tuần 4-5 |
| 3 | Tính năng thông minh (MVP) | 14-21 ngày | Tuần 7-8 |
| 4 | Xử lý dữ liệu & Integration | 14-21 ngày | Tuần 10-11 |
| 5 | Testing & Deployment | 7-10 ngày | Tuần 12 |

**Tổng thời gian:** 12-13 tuần (~3 tháng)

---

## CÔNG NGHỆ STACK TỔNG HỢP

### Backend
- Python 3.11
- FastAPI 0.109+
- SQLAlchemy 2.0 + Alembic
- PostgreSQL 16 + pgvector
- Redis 7
- Celery 5.x
- PyJWT, bcrypt

### Frontend
- Next.js 14 (App Router)
- TypeScript 5.x
- Tailwind CSS 3.x
- shadcn/ui
- Zustand
- TanStack Query
- React Hook Form + Zod

### Data & AI
- PyMuPDF (PDF extraction)
- python-docx
- spaCy (NER)
- sentence-transformers (optional embeddings)
- pandas (data processing)

### DevOps
- Docker + Docker Compose
- Apache Superset (BI dashboards)
- pytest (testing)
- GitHub Actions (CI/CD, optional)

---

## RỦI RO & GIẢI PHÁP

### Rủi ro 1: API bên thứ 3 thay đổi hoặc bị chặn
**Giải pháp:** 
- Có fallback sang HR-posted jobs
- Implement circuit breaker pattern
- Cache dữ liệu đã ingest

### Rủi ro 2: CV parsing không chính xác 100%
**Giải pháp:**
- Cho phép user edit parsed data
- Hiển thị confidence score
- Log errors để improve rule-based extractor

### Rủi ro 3: Matching algorithm đơn giản quá
**Giải pháp:**
- Start simple, measure accuracy
- Nếu cần, thêm vector embeddings sau
- Collect user feedback để tune weights

### Rủi ro 4: PostgreSQL performance với dữ liệu lớn
**Giải pháp:**
- Index đúng chỗ (GIN cho FTS, HNSW cho vectors)
- Partitioning nếu >100k rows
- Materialized views cho complex queries

### Rủi ro 5: Scope creep (thêm tính năng quá nhiều)
**Giải pháp:**
- Stick to MVP features
- Defer nice-to-haves (LTR, collaborative filtering)
- Time-box mỗi phase

---

## TIÊU CHÍ ĐÁNH GIÁ THÀNH CÔNG

### Functional Requirements
- [ ] User có thể đăng ký, đăng nhập, upload CV
- [ ] User có thể search và filter jobs
- [ ] User có thể apply cho jobs với CV đã upload
- [ ] HR có thể đăng tin tuyển dụng
- [ ] Hệ thống tự động parse CV và extract skills
- [ ] Hệ thống chấm điểm match giữa CV và JD
- [ ] Hệ thống gợi ý jobs phù hợp cho user
- [ ] Data được cập nhật tự động từ APIs bên ngoài

### Non-Functional Requirements
- [ ] Search response time < 800ms (p95)
- [ ] System handles 50 concurrent users
- [ ] 99% uptime trong demo period
- [ ] All technologies are free and open-source
- [ ] Deployable với single `docker compose up`
- [ ] Total RAM usage < 5GB

### Business Intelligence Requirements (cho môn học)
- [ ] Có ít nhất 3 Superset dashboards
- [ ] Dashboards show meaningful insights
- [ ] Data refreshes automatically
- [ ] Can explain data pipeline architecture

---

## BƯỚC TIẾP THEO NGAY

1. **Khởi tạo project structure:**
   ```bash
   mkdir job-suggestion
   cd job-suggestion
   mkdir frontend backend data
   ```

2. **Bắt đầu với Phase 1 (Frontend):**
   ```bash
   cd frontend
   npx create-next-app@latest . --typescript --tailwind --app
   npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu ...
   npx shadcn-ui@latest init
   ```

3. **Tạo mock data từ VietJobs dataset:**
   - Download từ Kaggle
   - Convert 50-100 records sang JSON format
   - Put in `frontend/mock/jobs.json`

Bạn có muốn tôi bắt đầu scaffold Phase 1 ngay bây giờ không?
