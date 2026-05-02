from passlib.context import CryptContext
import re
from app.core.config import settings
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)
def validate_password(password: str):
    if len(password) < 8:
        return "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return "Must include at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return "Must include at least one lowercase letter"

    if not re.search(r"[0-9]", password):
        return "Must include at least one number"

    if not re.search(r"[!@#$%^&*]", password):
        return "Must include a special character"
    return None

def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": data["sub"],
        "role": data.get("role"),
        "tv": data.get("tv"),
        "exp": expire,
        "type": "access"
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        **data,
        "exp": expire,
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
def create_reset_token(email: str) -> str:
    # Reset tokens should be short-lived (e.g., 15 minutes)
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "reset"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "reset":
            return None
        return payload.get("sub") # This is the user's email
    except JWTError:
        return None
