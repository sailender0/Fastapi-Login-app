from sqlalchemy.orm import Session
from app.db import models
from app.core.security import hash_password, verify_password

def create_user(db: Session, username: str, password: str):
    hashed = hash_password(password)
    user = models.User(username=username, password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user