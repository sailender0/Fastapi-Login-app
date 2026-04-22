from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from app.core.security import validate_password
from app.db.session import get_db
from app.db.models import User
from datetime import datetime, timedelta
import secrets
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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



@router.get("/")
def login_page(request: Request):
    
    user = request.cookies.get("session_user")

    if user:
        return RedirectResponse(url="/dashboard")

    csrf_token = secrets.token_hex(16)

    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "mode": "login",
            "csrf_token": csrf_token
        }
    )

    response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')

    return response

@router.get("/register")
def register_page(request: Request):
    csrf_token = secrets.token_hex(16)

    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "mode": "register",
            "csrf_token": csrf_token
        }
    )

    response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')

    return response
        

@router.post("/register")
def handle_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)):
    
    username = username.strip()
    password = password.strip()
    confirm_password = confirm_password.strip()
    
    if password != confirm_password:
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"mode": "register", "message": "Passwords do not match", "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response

    error = validate_password(password)
    if error:
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"mode": "register", "message": error, "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        logging.warning(f"REGISTER FAILED (duplicate): username={username}")
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"mode": "register", "message": "Username already exists", "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response
    safe_password = password.strip()[:72]
    hashed = pwd_context.hash(safe_password)

    new_user = User(username=username, hashed_password=hashed)
    db.add(new_user)

    try:
        db.commit()
        logging.info(f"NEW USER REGISTERED: username={username}")
    except Exception:
        db.rollback()
        logging.warning(f"REGISTER FAILED: username={username}")
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"mode": "register", "message": "Username already taken", "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response

    csrf_token = secrets.token_hex(16)
    response = templates.TemplateResponse(
        request,
        "index.html",
        {"message": "Account created! Please log in.", "mode": "login", "csrf_token": csrf_token}
    )
    response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
    return response


@router.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    username = username.strip()
    password = password.strip()
    cookie_token = request.cookies.get("csrf_token")

    if not csrf_token or csrf_token != cookie_token:
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"mode": "login", "message": "Invalid CSRF token", "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response
    ip = request.client.host
    logging.info(f"LOGIN ATTEMPT: username={username}, ip={ip}")
    attempt = login_attempts.get(ip)
    attempt = login_attempts.get(ip)
    if attempt:
        if attempt["count"] >= MAX_ATTEMPTS and datetime.utcnow() < attempt["lock_until"]:
            csrf_token = secrets.token_hex(16)
            response = templates.TemplateResponse(
                request,
                "index.html",
                {"message": "Too many failed attempts. Try again later.", "mode": "login", "csrf_token": csrf_token}
            )
            response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
            return response

    db_user = db.query(User).filter(User.username == username).first()

    if not db_user or not pwd_context.verify(password.strip()[:72], db_user.hashed_password):

        if ip not in login_attempts:
            login_attempts[ip] = {
                "count": 1,
                "lock_until": datetime.utcnow() + LOCK_TIME
            }
        else:
            login_attempts[ip]["count"] += 1
            login_attempts[ip]["lock_until"] = datetime.utcnow() + LOCK_TIME
        logging.warning(f"FAILED LOGIN ATTEMPT: username={username}, ip={ip}")
        csrf_token = secrets.token_hex(16)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {"message": "Invalid username or password", "mode": "login", "csrf_token": csrf_token}
        )
        response.set_cookie("csrf_token", csrf_token, httponly=True, secure=False, samesite='lax')
        return response

    login_attempts.pop(ip, None)
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

    return templates.TemplateResponse(
        request,
        "index.html",
        {"username": user}
    )

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_user")
    return response