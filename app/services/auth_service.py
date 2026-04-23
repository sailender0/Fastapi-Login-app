from sqlalchemy.orm import Session
import logging
from app.db import models
from app.core.security import hash_password, verify_password
from sqlalchemy.exc import IntegrityError

def create_user(db: Session, username: str, password: str):
    username = username.strip()
    # limit password to bcrypt-friendly length
    safe_password = password.strip()[:72]
    logging.info("create_user: creating user with username='%s' (len password=%d)", username, len(safe_password))
    hashed = hash_password(safe_password)
    user = models.User(username=username, hashed_password=hashed)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logging.info("create_user: created user id=%s username='%s'", user.id, user.username)
        return user
    except IntegrityError:
        db.rollback()
        raise


def authenticate_user(db: Session, username: str, password: str):
    username = username.strip()
    logging.info("authenticate_user: attempt username='%s'", username)
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        logging.info("authenticate_user: user not found username='%s'", username)
        return None

    safe_password = password.strip()[:72]
    if not verify_password(safe_password, user.hashed_password):
        logging.info("authenticate_user: password mismatch for username='%s'", username)
        return None

    logging.info("authenticate_user: success for username='%s' id=%s", username, user.id)
    return user


def get_user_by_username(db: Session, username: str):
    username = username.strip()
    return db.query(models.User).filter(models.User.username == username).first()