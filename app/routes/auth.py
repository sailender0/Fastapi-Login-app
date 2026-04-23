from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import secrets
from app.core.security import validate_password
from app.db.session import get_db
from app.services.auth_service import create_user, authenticate_user, get_user_by_username
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
login_attempts = {}

MAX_ATTEMPTS = 5
LOCK_TIME = timedelta(minutes=5)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def make_csrf_response(request: Request, context: dict, template_name: str = "index.html"):
    csrf_token = secrets.token_hex(16)
    context = dict(context)
    context["csrf_token"] = csrf_token
    response = templates.TemplateResponse(request, template_name, context)
    response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
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
def login_page(request: Request):
    user = request.cookies.get("session_user")
    if user:
        return RedirectResponse(url="/dashboard")
    return render_csrf(request, mode="login")


@router.get("/register")
def register_page(request: Request):
    return render_csrf(request, mode="register")


@router.post("/register")
def handle_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    password = password.strip()
    confirm_password = confirm_password.strip()

    if password != confirm_password:
        return render_csrf(request, mode="register", message="Passwords do not match")

    error = validate_password(password)
    if error:
        return render_csrf(request, mode="register", message=error)

    existing_user = get_user_by_username(db, username)
    if existing_user:
        logging.warning(f"REGISTER FAILED (duplicate): username={username}")
        return render_csrf(request, mode="register", message="Username already exists")

    try:
        user = create_user(db, username, password)
        logging.info(f"NEW USER REGISTERED: username={user.username}")
    except IntegrityError:
        logging.warning(f"REGISTER FAILED (integrity): username={username}")
        return render_csrf(request, mode="register", message="Username already taken")

    return render_csrf(request, mode="login", message="Account created! Please log in.")


@router.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
):
    username = username.strip()
    password = password.strip()
    cookie_token = request.cookies.get("csrf_token")

    if not csrf_token or csrf_token != cookie_token:
        return render_csrf(request, mode="login", message="Invalid CSRF token")

    ip = request.client.host
    key = f"{ip}:{username}"
    logging.info(f"LOGIN ATTEMPT: username={username}, ip={ip}")
    attempt = login_attempts.get(key)
    if attempt and attempt["count"] >= MAX_ATTEMPTS and datetime.now(timezone.utc) < attempt["lock_until"]:
        return render_csrf(request, mode="login", message="Too many failed attempts. Try again later.")

    db_user = authenticate_user(db, username, password)
    if not db_user:
        if key not in login_attempts:
            login_attempts[key] = {"count": 1, "lock_until": datetime.now(timezone.utc) + LOCK_TIME}
        else:
            login_attempts[key]["count"] += 1
            login_attempts[key]["lock_until"] = datetime.now(timezone.utc) + LOCK_TIME
        logging.warning(f"FAILED LOGIN ATTEMPT: username={username}, ip={ip}")
        return render_csrf(request, mode="login", message="Invalid username or password")

    # on successful login, clear attempts for this ip+username key
    login_attempts.pop(key, None)
    logging.info(f"SUCCESS LOGIN: username={username}, ip={ip}")
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_user",
        value=username,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.get("/dashboard")
def dashboard(request: Request):
    user = request.cookies.get("session_user")
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "index.html", {"username": user})


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_user")
    return response
