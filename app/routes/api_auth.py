from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserLogin, UserPublic, TokenResponse
from app.services.auth_service import create_user, authenticate_user, get_user_by_username
from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic, status_code=201)
async def api_register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    try:
        user = await create_user(db, body.username, body.password)
        return user
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")

@router.post("/login", response_model=TokenResponse)
async def api_login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserPublic)
async def api_me(current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, current["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
