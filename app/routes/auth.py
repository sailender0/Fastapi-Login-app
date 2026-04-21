from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates

from app.db.session import get_db
from app.db.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
# LOGIN PAGE
# -------------------------
@router.get("/")
def login_page(request: Request):
    user = request.cookies.get("session_user")

    if user:
        return RedirectResponse(url="/dashboard")

    return templates.TemplateResponse(
        request,
        "index.html",
        {"mode": "login"}
    )

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"mode": "register"}
    )

@router.post("/register")
def handle_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    safe_password = password.strip()[:72]
    hashed = pwd_context.hash(safe_password)

    new_user = User(username=username, hashed_password=hashed)
    db.add(new_user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "message": "Username already taken",
                "mode": "register"
            }
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "message": "Account created! Please log in.",
            "mode": "login"
        }
    )


@router.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()

    if db_user and pwd_context.verify(password.strip()[:72], db_user.hashed_password):

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="session_user",
            value=username,
            httponly=True,
            
        )
        return response

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "message": "Invalid username or password",
            "mode": "login"
        }
    )


@router.get("/dashboard")
def dashboard(request: Request):
    user = request.cookies.get("session_user")

    if not user:
        return RedirectResponse(url="/")

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "username": user
        }
    )

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session_user")
    return response