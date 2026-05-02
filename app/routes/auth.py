from sqlalchemy.future import select
from fastapi import APIRouter, BackgroundTasks, Request, Form, Depends
from fastapi.responses import RedirectResponse
from httpx import request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from app.core.security import decode_reset_token, validate_password, hash_password, create_reset_token
from app.db.session import get_db
from app.db.models import User
from app.dependencies.rate_limit import rate_limit_dependency
from app.services.rate_limiter import check_rate_limit, register_failure, register_success
from app.services.auth_service import create_user, authenticate_user, get_user_by_email, get_user_by_username
from app.services.email_service import send_mfa_email, send_welcome_email, send_reset_email
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr, TypeAdapter, ValidationError
import logging
import pyotp
import secrets



router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
email_validator = TypeAdapter(EmailStr)

def make_csrf_response(request: Request, context: dict, template_name: str = "index.html"):
    csrf_token = secrets.token_hex(16)  #generate the csrf token
    context = dict(context)
    context["csrf_token"] = csrf_token
    response = templates.TemplateResponse(request=request, name=template_name, context=context)
    response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')# store the  token in the cookie
    return response


def render_csrf(request: Request, mode: str = None, message: str = None, template_name: str = "index.html", extra: dict = None):
    ctx = {}
    if mode:
        ctx["mode"] = mode
    if message:
        ctx["message"] = message
    if extra:
        ctx.update(extra)
    return make_csrf_response(request, ctx, template_name)

@router.get("/")
async def login_page(request: Request, message: str = None):
    user = request.cookies.get("session_user")
    if user:
        return RedirectResponse(url="/dashboard")
    
    # Pass the message into the render function
    return render_csrf(request, mode="login", message=message)


@router.get("/register")
async def register_page(request: Request):
    return render_csrf(request, mode="register")



@router.post("/register")
async def handle_register(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    confirm_password: str = Form(...),
     csrf_token: str = Form(None),
    db: AsyncSession = Depends(get_db),
    
):
    username = username.strip()
    password = password.strip()
    email = email.strip().lower()
    confirm_password = confirm_password.strip()
    cookie_token = request.cookies.get("csrf_token")
    if not csrf_token or csrf_token != cookie_token:
        return render_csrf(request=request,mode="register",message="Invalid CSRF token")
    
    try:
        email_validator.validate_python(email)
    except ValidationError:
        return render_csrf(request=request, mode="register", message="Invalid email format", 
                           extra={"form_data": {"username": username, "email": email}})
    if password != confirm_password:
        return render_csrf(request,mode="register",message="Passwords do not match",extra={"form_data": {"username": username, "email": email}})
    error = validate_password(password)
    if error:
        return render_csrf(request=request, mode="register", message=error)
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        logging.warning(f"REGISTER FAILED (duplicate): username={username}")
        return render_csrf(request=request, mode="register", message="Username already exists")
    if await get_user_by_email(db, email):
        return render_csrf(request=request, mode="register", message="Email already registered")
    
    try:
        user = await create_user(db,username,email,password)
        background_tasks.add_task(send_welcome_email, email, username)
        logging.info(f"NEW USER REGISTERED: username={user.username}")
    except IntegrityError:
        logging.warning(f"REGISTER FAILED (integrity): username={username}")
        return render_csrf(request=request, mode="register", message="Username already taken")
    return RedirectResponse(
    url="/?message=Account+created!+Please+check+your+email.", 
    status_code=303
)

@router.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(None),
    db: AsyncSession = Depends(get_db),
    rate_data = Depends(rate_limit_dependency)):
    
    username = username.strip()
    password = password.strip()
    cookie_token = request.cookies.get("csrf_token")

    if not csrf_token or csrf_token != cookie_token:
        return render_csrf(request=request, mode="login", message="Invalid CSRF token")
    if not rate_data["allowed"]:
        return render_csrf(request=request,mode="login",message=f"Too many login attempts. Try again in {rate_data['retry_after']} seconds.")
    ip = request.client.host
    logging.info(f"LOGIN ATTEMPT: username={username}, ip={ip}")
    db_user = await authenticate_user(db, username, password)

    if not db_user:
        await register_failure(ip, username)
        logging.warning(f"FAILED LOGIN: username={username}, ip={ip}")
        return render_csrf(request=request,mode="login",message="Invalid username or password" )
    secret = pyotp.random_base32() 
    totp = pyotp.TOTP(secret, interval=300) # Valid for 5 mins
    otp_code = totp.now()

    # 2. Send the email using your existing App Password setup
    try:
        await send_mfa_email(db_user.email, otp_code)
    except Exception as e:
        logging.error(f"Mail failed: {e}")
        return render_csrf(request, mode="login", message="Error sending verification email.")

    # 3. Redirect to the MFA verification page
    response = render_csrf(request, mode="verify_mfa", message="Please enter the code sent to your email.")
    response.set_cookie(key="mfa_user", value=db_user.username, httponly=True, max_age=300)
    response.set_cookie(key="mfa_secret", value=secret, httponly=True, max_age=300)
    
    return response
    
@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    otp_code: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Retrieve the temporary info from cookies
    username = request.cookies.get("mfa_user")
    secret = request.cookies.get("mfa_secret")

    if not username or not secret:
        return render_csrf(request, mode="login", message="Session expired. Please login again.")

    # 2. Verify the 6-digit code
    totp = pyotp.TOTP(secret, interval=300)
    if not totp.verify(otp_code):
        return render_csrf(request, mode="verify_mfa", message="Invalid or expired code.")
    # 3. Success! Fetch user to get their role and issue the real session cookies
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username))
    db_user = result.scalars().first()

    if not db_user:
        return render_csrf(request, mode="login", message="User not found.")
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_user", value=db_user.username, httponly=True)
    response.set_cookie(key="session_role", value=db_user.role, httponly=True)
    response.delete_cookie("mfa_user")
    response.delete_cookie("mfa_secret")
    
    logging.info(f"MFA SUCCESS: username={username}")
    return response
@router.get("/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    username = request.cookies.get("session_user")
    
    if not username:
        return RedirectResponse(url="/")

    user = await get_user_by_username(db, username)

    if not user:
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "username": user.username,
            "role": user.role
        }
    )
@router.get("/reset-password")
async def handle_reset_password(request: Request, token: Optional[str] = None):
    if token :
        email = decode_reset_token(token)
        if not email:
            return render_csrf(request, mode="login", message="Reset link is invalid or expired.")
    
    # Show the reset form and pass the token forward
        return render_csrf(request, mode="reset_password_form", extra={"token": token})
    return render_csrf(request, mode="forgot_password")
# 1. This handles the "Enter your email" form submission
@router.post("/reset-password-request") # Changed the URL slightly
async def handle_forgot_password(
    request: Request, 
    email: str = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    query=select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if user:
        token = create_reset_token(email)
        # Make sure the link in the email points back to /reset-password
        reset_link = f"{request.base_url}reset-password?token={token}"
        await send_reset_email(email, reset_link)
    
    return render_csrf(request, mode="login", message="If that email exists, a reset link has been sent.")


@router.post("/reset-password")
async def handle_password_reset(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
   
    # 1. Verify the token again on submission
    email = decode_reset_token(token)
    if not email:
        return render_csrf(request, mode="login", message="Session expired. Please try again.")

    if new_password != confirm_password:
        return render_csrf(request, mode="reset_password_form", extra={"token": token}, message="Passwords do not match.")

    # 2. Update the user in the database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user:
        user.hashed_password = hash_password(new_password)
        await db.commit()
        return render_csrf(request, mode="login", message="Password updated! Please login.")
    
    return render_csrf(request, mode="login", message="An error occurred.")
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_user")
    response.delete_cookie("session_role")
    return response
