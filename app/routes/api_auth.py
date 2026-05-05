from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import UserCreate, UserLogin, UserPublic, TokenResponse
from app.services.auth_service import create_user, authenticate_user, get_user_by_username, get_all_users
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.schemas.auth import  RefreshRequest
from app.dependencies.auth import get_current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.core.rbac import require_roles

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic, status_code=201)
async def api_register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")
    try:
        user = await create_user(db, body.username,body.email, body.password)
        return user
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Username or email already taken")

@router.post("/login", response_model=TokenResponse)
async def api_login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
    data={
        "sub": user.username,
        "role": user.role,
        "tv": user.token_version
    }
)
    refresh_token = create_refresh_token({"sub": user.username})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
    
@router.get("/me")
async def api_me(current=Depends(get_current_user)):
    return current

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_refresh_token(body.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    username = payload.get("sub")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "tv": user.token_version
    })

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=body.refresh_token, 
        token_type="bearer"
    )
@router.get("/admin/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current=Depends(require_roles("admin"))
):
    try:
        # 1. Use the async-safe query
        result = await db.execute(select(User))
        users = result.scalars().all()

        # 2. Build the list. 
        # If this line crashes, check if 'u' has the attributes you expect
        user_list = []
        for u in users:
            user_list.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role
            })
            
        return user_list

    except Exception as e:
        # 3. This will print the REAL error in your terminal window
        print(f"--- BACKEND ERROR ---: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error in User List")
