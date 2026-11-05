from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..db import connect, RealDictCursor
from ..security import hash_password, verify_password, make_token, current_user

router = APIRouter(prefix="/api/v1", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None


def _public(u: dict, full_name: Optional[str] = None) -> dict:
    return {"id": str(u["id"]), "email": u["email"], "role": u["role"],
            "company_id": u.get("company_id"), "full_name": full_name or u["email"]}


def _full_name(cur, u: dict) -> Optional[str]:
    cur.execute("SELECT full_name FROM candidate WHERE user_id=%s", (u["id"],))
    r = cur.fetchone()
    if r:
        return r["full_name"]
    if u.get("company_id"):
        cur.execute("SELECT name FROM company WHERE id=%s", (u["company_id"],))
        r = cur.fetchone()
        return r["name"] if r else None
    return None


@router.post("/auth/login")
def login(req: LoginRequest):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email=%s", (req.email.lower().strip(),))
        u = cur.fetchone()
        if not u or not verify_password(req.password, u["password_hash"]):
            raise HTTPException(401, "Invalid credentials")
        return {"access_token": make_token(u), "token_type": "bearer",
                "user": _public(u, _full_name(cur, u))}
    finally:
        conn.close()


@router.post("/auth/register")
def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password too short (min 6)")
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT 1 FROM users WHERE email=%s", (req.email.lower().strip(),))
        if cur.fetchone():
            raise HTTPException(400, "Email already registered")
        cur.execute("INSERT INTO users (email,password_hash,role) VALUES (%s,%s,'candidate') RETURNING *",
                    (req.email.lower().strip(), hash_password(req.password)))
        u = cur.fetchone()
        cur.execute("INSERT INTO candidate (user_id, full_name) VALUES (%s,%s)", (u["id"], req.full_name))
        conn.commit()
        return _public(u, req.full_name)
    finally:
        conn.close()


@router.get("/users/me")
def me(user: dict = Depends(current_user)):
    conn = connect(retries=3)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id=%s", (user["id"],))
        u = cur.fetchone()
        if not u:
            raise HTTPException(401, "User not found")
        return _public(u, _full_name(cur, u))
    finally:
        conn.close()
