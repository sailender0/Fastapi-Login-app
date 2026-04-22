from passlib.context import CryptContext
import re
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