"""Password hashing + JWT helpers."""
import os
import time
import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-please-32bytes!!")
ALGO = "HS256"
_bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt(rounds=10)).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def make_token(user: dict, ttl: int = 86400) -> str:
    payload = {"sub": str(user["id"]), "role": user["role"],
               "company_id": user.get("company_id"), "exp": int(time.time()) + ttl}
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def current_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(401, "Not authenticated")
    try:
        p = jwt.decode(cred.credentials, SECRET, algorithms=[ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    return {"id": int(p["sub"]), "role": p["role"], "company_id": p.get("company_id")}


def optional_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    try:
        return current_user(cred)
    except HTTPException:
        return None


def require_role(*roles):
    def dep(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, "Forbidden")
        return user
    return dep
