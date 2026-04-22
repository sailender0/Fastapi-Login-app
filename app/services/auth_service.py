from sqlalchemy.orm import Session
from app.db import models
from app.core.security import hash_password, verify_password

def create_user(db: Session, username: str, password: str):
    username = username.strip()
    # limit password to bcrypt-friendly length
    safe_password = password.strip()[:72]
    hashed = hash_password(safe_password)
    user = models.User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    username = username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return None

    safe_password = password.strip()[:72]
    if not verify_password(safe_password, user.hashed_password):
        return None

    return user