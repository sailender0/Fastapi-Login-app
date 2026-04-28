from passlib.context import CryptContext
import re
from app.core.config import settings
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.core.config import settings


SECRET_KEY = settings.SECRET_KEY
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
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None
