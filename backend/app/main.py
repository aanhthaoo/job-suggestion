from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os

# Import matching and CV parser
from .matching import calculate_match_score, recommend_jobs_for_user
from .cv_parser import parse_cv

# Load mock data.
# __file__ is backend/app/main.py, so two levels up is the project root locally.
_HERE = os.path.dirname(__file__)
_MOCK_CANDIDATES = [
    os.environ.get('MOCK_JOBS_FILE'),          # explicit override (compose)
    os.path.join(_HERE, '..', '..', 'frontend', 'mock', 'jobs.json'),  # local dev
    '/app/frontend/mock/jobs.json',            # compose volume mount
    '/app/mock_jobs.json',                     # legacy copy location
]

MOCK_JOBS_FILE = next((p for p in _MOCK_CANDIDATES if p and os.path.exists(p)), None)

if MOCK_JOBS_FILE is None:
    # Last resort: inline mock data
    MOCK_JOBS = [
        {
            "id": "1",
            "title": "Senior Python Developer",
            "company_id": "1",
            "company_name": "TechViet Solutions",
            "description": "Phát triển backend services sử dụng Python, FastAPI, PostgreSQL.",
            "requirements": "- Tối thiểu 3 năm kinh nghiệm Python\n- Thành thạo FastAPI/Django",
            "skills_required": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
            "location": "Hà Nội",
            "salary_min": 25000000,
            "salary_max": 40000000,
            "currency": "VND",
            "experience_years": 3,
            "job_type": "fulltime",
            "work_mode": "hybrid",
            "status": "active",
            "posted_at": "2026-10-20T08:00:00Z"
        }
    ]
else:
    with open(MOCK_JOBS_FILE, 'r', encoding='utf-8') as f:
        MOCK_JOBS = json.load(f)

app = FastAPI(title="JobPortal API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None

class User(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "candidate"

class JobResponse(BaseModel):
    id: str
    title: str
    company_name: Optional[str] = None
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "VND"
    experience_years: int
    job_type: str
    work_mode: str
    skills_required: List[str]
    posted_at: str
    match_score: Optional[float] = None

class JobDetail(JobResponse):
    description: str
    requirements: str
    company_id: str
    status: str

# Mock users database
MOCK_USERS = {
    "admin@test.com": {"id": "1", "email": "admin@test.com", "full_name": "Admin User", "role": "admin", "password": "admin123"},
    "user@test.com": {"id": "2", "email": "user@test.com", "full_name": "Test User", "role": "candidate", "password": "user123"},
}

# Auth endpoints
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    user_data = MOCK_USERS.get(request.email)
    if not user_data or user_data["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(id=user_data["id"], email=user_data["email"], full_name=user_data["full_name"], role=user_data["role"])
    return {
        "access_token": "mock-jwt-token-" + user.id,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    if request.email in MOCK_USERS:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(len(MOCK_USERS) + 1)
    user = User(id=user_id, email=request.email, full_name=request.full_name)
    MOCK_USERS[request.email] = {
        "id": user_id,
        "email": request.email,
        "full_name": request.full_name,
        "role": "candidate",
        "password": request.password,
    }
    
    return user

# Jobs endpoints
@app.get("/api/v1/jobs")
async def list_jobs(
    search: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    jobs = MOCK_JOBS
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        jobs = [j for j in jobs if 
                search_lower in j["title"].lower() or 
                search_lower in j.get("company_name", "").lower() or
                any(search_lower in skill.lower() for skill in j["skills_required"])]
    
    # Filter by location
    if location:
        jobs = [j for j in jobs if location.lower() in j["location"].lower()]
    
    # Filter by job_type
    if job_type:
        jobs = [j for j in jobs if j["job_type"] == job_type]
    
    # Filter by work_mode
    if work_mode:
        jobs = [j for j in jobs if j["work_mode"] == work_mode]
    
    # Pagination
    total = len(jobs)
    start = (page - 1) * limit
    end = start + limit
    paginated_jobs = jobs[start:end]
    
    return {
        "items": paginated_jobs,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    job = next((j for j in MOCK_JOBS if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# User endpoints
@app.get("/api/v1/users/me")
async def get_current_user():
    # For demo, return mock user
    return User(id="2", email="user@test.com", full_name="Test User", role="candidate")

# Applications endpoints (mock)
@app.get("/api/v1/applications")
async def get_applications():
    return []

@app.post("/api/v1/applications")
async def apply_to_job():
    return {"id": "1", "status": "submitted", "applied_at": datetime.utcnow().isoformat()}

# Saved jobs endpoints (mock)
@app.get("/api/v1/saved-jobs")
async def get_saved_jobs():
    return []

@app.post("/api/v1/saved-jobs")
async def save_job():
    return {"id": "1"}

@app.delete("/api/v1/saved-jobs/{job_id}")
async def unsave_job(job_id: str):
    return None

# Admin endpoints (mock)
@app.get("/api/v1/admin/stats")
async def admin_stats():
    return {
        "postgres_status": "connected",
        "redis_status": "connected",
        "celery_status": "active",
        "total_jobs": len(MOCK_JOBS),
        "total_users": len(MOCK_USERS),
        "today_applications": 5
    }

@app.get("/api/v1/admin/tasks")
async def admin_tasks():
    return [
        {
            "name": "ingest_greenhouse_jobs",
            "status": "Succeeded",
            "started_at": "2026-10-22T12:00:00Z",
            "duration": "45s",
            "result": "+23 jobs"
        },
        {
            "name": "reconcile_jobs",
            "status": "Running",
            "started_at": "2026-10-22T13:00:00Z",
            "duration": "12s",
            "result": None
        }
    ]

@app.post("/api/v1/admin/tasks/sync-now")
async def trigger_sync():
    return {"task_id": "mock-task-id"}

# Smart Features - Matching & CV Parsing

class MatchScoreRequest(BaseModel):
    cv_skills: List[str]
    cv_experience_years: float = 0
    cv_location: str = ""
    job_id: str

@app.post("/api/v1/match/calculate")
async def calculate_match(request: MatchScoreRequest):
    """Calculate match score between user profile and a specific job"""
    job = next((j for j in MOCK_JOBS if j['id'] == request.job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    cv_data = {
        'skills': request.cv_skills,
        'experience_years': request.cv_experience_years,
        'location': request.cv_location,
    }
    
    score, reason = calculate_match_score(cv_data, job)
    
    return {
        'job_id': request.job_id,
        'score': score,
        'reason': reason
    }

@app.get("/api/v1/recommendations")
async def get_recommendations(
    skills: Optional[str] = None,
    experience_years: float = 0,
    location: str = "",
    top_k: int = 10
):
    """Get personalized job recommendations"""
    # Build user profile from query params
    user_profile = {
        'skills': skills.split(',') if skills else [],
        'experience_years': experience_years,
        'location': location,
    }
    
    recommendations = recommend_jobs_for_user(user_profile, MOCK_JOBS, top_k)
    
    return {
        'recommendations': [
            {
                'job': job,
                'score': score
            }
            for job, score in recommendations
        ]
    }

class CVParseResponse(BaseModel):
    skills: List[str]
    experience_years: float
    education: List[str]
    text_preview: str

@app.post("/api/v1/cv/parse")
async def parse_cv_endpoint(file: UploadFile = File(...)):
    """Parse uploaded CV file and extract information"""
    # Save uploaded file temporarily
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Determine file type
        file_type = file.filename.split('.')[-1].lower()
        if file_type not in ['pdf', 'docx']:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Parse CV
        result = parse_cv(file_path, file_type)
        
        return CVParseResponse(
            skills=result['skills'],
            experience_years=result['experience_years'],
            education=result['education'],
            text_preview=result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
        )
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
