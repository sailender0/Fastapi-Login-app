from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.db import models
from app.core.security import hash_password, verify_password
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import asyncio
from app.db.models import User

async def create_user(db: AsyncSession, username: str,email: str, password: str):
    username = username.strip()
    email = email.strip()
    safe_password = password.strip()[:72]
    logging.info("create_user: creating user with username='%s' email='%s' (len password=%d)", username, email, len(safe_password))
    # run hashing in threadpool to avoid blocking event loop
    hashed = await asyncio.to_thread(hash_password, safe_password)
    user = models.User(username=username,email=email, hashed_password=hashed)
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logging.info("create_user: created user id=%s username='%s'", user.id, user.username)
        return user
    except IntegrityError:
        await db.rollback()
        raise

async def authenticate_user(db: AsyncSession, username: str, password: str):
    username = username.strip()
    logging.info("authenticate_user: attempt username='%s'", username)
    q = select(models.User).where(models.User.username == username)
    res = await db.execute(q)
    user = res.scalar_one_or_none()

    if not user:
        logging.info("authenticate_user: user not found username='%s'", username)
        return None

    safe_password = password.strip()[:72]
    verified = await asyncio.to_thread(verify_password, safe_password, user.hashed_password)
    if not verified:
        logging.info("authenticate_user: password mismatch for username='%s'", username)
        return None
    logging.info("authenticate_user: success for username='%s' id=%s", username, user.id)
    return user

async def get_user_by_username(db: AsyncSession, username: str):
    username = username.strip()
    q = select(models.User).where(models.User.username == username)
    res = await db.execute(q)
    return res.scalar_one_or_none()

async def update_user_role(db: AsyncSession, username: str, new_role: str):
    user = await get_user_by_username(db, username)

    if not user:
        raise Exception("User not found")

    user.role = new_role
    user.token_version += 1
    await db.commit()
    await db.refresh(user)
    return user

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user_by_email(db: AsyncSession, email: str):
    email = email.strip().lower()
    q = select(models.User).where(models.User.email == email)
    res = await db.execute(q)
    return res.scalar_one_or_none()
