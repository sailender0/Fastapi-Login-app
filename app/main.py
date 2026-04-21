from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.routes import auth

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
