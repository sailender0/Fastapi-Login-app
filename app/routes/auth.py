from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
import secrets
from app.core.security import validate_password
from app.db.session import get_db
from app.dependencies.rate_limit import rate_limit_dependency
from app.services.rate_limiter import check_rate_limit, register_failure, register_success
from app.services.auth_service import create_user, authenticate_user, get_user_by_username
from sqlalchemy.exc import IntegrityError
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
async def login_page(request: Request):
    user = request.cookies.get("session_user")
    if user:
        return RedirectResponse(url="/dashboard")
    return render_csrf(request, mode="login")

@router.get("/register")
async def register_page(request: Request):
    return render_csrf(request, mode="register")

@router.post("/register")
async def handle_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
     csrf_token: str = Form(None),
    db: AsyncSession = Depends(get_db),
    
):
    username = username.strip()
    password = password.strip()
    confirm_password = confirm_password.strip()
    cookie_token = request.cookies.get("csrf_token")
    if not csrf_token or csrf_token != cookie_token:
        return render_csrf(
        request=request,
        mode="register",
        message="Invalid CSRF token"
    )
    if password != confirm_password:
        return render_csrf(request=request, mode="register", message="Passwords do not match")
    error = validate_password(password)
    if error:
        return render_csrf(request=request, mode="register", message=error)
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        logging.warning(f"REGISTER FAILED (duplicate): username={username}")
        return render_csrf(request=request, mode="register", message="Username already exists")
    try:
        user = await create_user(db, username, password)
        logging.info(f"NEW USER REGISTERED: username={user.username}")
    except IntegrityError:
        logging.warning(f"REGISTER FAILED (integrity): username={username}")
        return render_csrf(request=request, mode="register", message="Username already taken")
    return render_csrf(request=request, mode="login", message="Account created! Please log in.")

@router.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(None),
    db: AsyncSession = Depends(get_db),
    rate_data = Depends(rate_limit_dependency)
    
):
    username = username.strip()
    password = password.strip()
    cookie_token = request.cookies.get("csrf_token")

    if not csrf_token or csrf_token != cookie_token:
        return render_csrf(request=request, mode="login", message="Invalid CSRF token")
    if not rate_data["allowed"]:
        return render_csrf(
            request=request,
            mode="login",
            message=f"Too many login attempts. Try again in {rate_data['retry_after']} seconds."
        )
    ip = request.client.host
    logging.info(f"LOGIN ATTEMPT: username={username}, ip={ip}")
    db_user = await authenticate_user(db, username, password)

    if not db_user:
        await register_failure(ip, username)
        logging.warning(f"FAILED LOGIN: username={username}, ip={ip}")
        return render_csrf(
            request=request,
            mode="login",
            message="Invalid username or password"
        )
    await register_success(ip, username)
    logging.info(f"SUCCESS LOGIN: username={username}, ip={ip}")
    response = RedirectResponse(url="/dashboard", status_code=302)

    response.set_cookie(
        key="session_user",
        value=username,
        httponly=True,
        secure=False,      
    )

    return response

@router.get("/dashboard")
async def dashboard(request: Request):
    user = request.cookies.get("session_user")
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request=request, name="index.html", context={"username": user})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_user")
    return response
