"""
Authentication: email + password accounts with JWT bearer tokens.

Passwords are hashed with scrypt (stdlib — no extra dependency), tokens are
HS256 JWTs valid for 7 days. Every data route depends on `current_user`,
and every document is scoped to the owning user_id.
"""

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from db import users

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_TTL_DAYS = 7
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_bearer = HTTPBearer(auto_error=False)


# ── Password hashing (scrypt, per-user salt) ─────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":")
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


# ── Tokens ────────────────────────────────────────────────────────────────────

def make_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_TTL_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """FastAPI dependency: resolves the bearer token to {user_id, email} or 401s."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"user_id": payload["sub"], "email": payload["email"]}


# ── Endpoints ─────────────────────────────────────────────────────────────────

class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)


@router.post("/auth/register")
def register(body: Credentials):
    email = body.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    result = users.insert_one({
        "email": email,
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc),
    })
    user_id = str(result.inserted_id)
    return {"token": make_token(user_id, email), "email": email}


@router.post("/auth/login")
def login(body: Credentials):
    email = body.email.strip().lower()
    user = users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        # Same message either way — don't reveal which emails exist
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"token": make_token(str(user["_id"]), email), "email": email}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user
