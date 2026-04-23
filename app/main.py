from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.routes import auth
from app.db.session import init_db

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)


@app.on_event("startup")
async def startup():
    await init_db()