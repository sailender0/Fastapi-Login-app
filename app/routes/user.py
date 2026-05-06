from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status, Form, File
from app.db.models import User
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import  update
from app.db.session import get_db
from app.db.models import User
import os
import uuid
from app.schemas.auth import ProfileUpdate, ProfileRead
from app.dependencies.auth import get_current_user # Your JWT helper

router = APIRouter(prefix="/profile", tags=["Profile"])
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "static/profile_pics"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me", response_model=ProfileRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetch the logged-in user's profile info"""
    return current_user

@router.post("/update")
async def update_profile(
    full_name: str = Form(None),
    bio: str = Form(None),
    profile_pic: UploadFile = File(None), # New File parameter
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = {}
    if full_name: update_data["full_name"] = full_name
    if bio: update_data["bio"] = bio

    # Handle Image Upload
    if profile_pic and profile_pic.filename:
        # Generate unique filename: user_id + uuid + extension
        ext = os.path.splitext(profile_pic.filename)[1]
        filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file to local disk
        with open(file_path, "wb") as buffer:
            content = await profile_pic.read()
            buffer.write(content)
        
        # Save the URL path to the database
        update_data["profile_image"] = f"/static/profile_pics/{filename}"

    if not update_data:
        return RedirectResponse(url="/dashboard", status_code=303)

    query = update(User).where(User.id == current_user.id).values(**update_data)
    
    try:
        await db.execute(query)
        await db.commit()
        return RedirectResponse(url="/dashboard?message=Profile+Updated", status_code=303)
    except Exception:
        await db.rollback()
        return RedirectResponse(url="/dashboard?message=Update+Failed", status_code=303)
@router.get("/profile")
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "bio": current_user.bio,
        "profile_image": current_user.profile_image,
        "message": request.query_params.get("message")
    })
