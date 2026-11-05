import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import admin, applications, auth, candidate, cv, employer, jobs, match

app = FastAPI(title="JobPortal API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, jobs.router, cv.router, candidate.router, match.router,
          applications.router, employer.router, admin.router):
    app.include_router(r)


@app.get("/health")
def health():
    return {"status": "ok"}
