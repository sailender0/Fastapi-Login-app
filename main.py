from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine) # Creates the users.db file

# --- SECURITY SETUP ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# This helps us talk to the database safely
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )

@app.post("/login")
def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):

    if username == "admin" and password == "1234":
       return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"message": "Login successful"}
)

    return templates.TemplateResponse(
    request=request,
    name="login.html",
    context={"message": "Invalid credentials"}
)
@app.post("/register")
def handle_register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    safe_password = password.strip()[:72]
    hashed = pwd_context.hash(password)
    
    new_user = User(username=username, hashed_password=hashed)
    
    db.add(new_user)
    db.commit()
    
    return {"message": f"User {username} created! Now go back to the login page."}