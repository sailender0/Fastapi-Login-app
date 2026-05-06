import logging
from fastapi import FastAPI
from app.routes import auth, user
from app.db.session import init_db
from app.routes import api_auth
from fastapi.staticfiles import StaticFiles


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
app = FastAPI()
app.include_router(auth.router)
app.include_router(api_auth.router)
app.include_router(user.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.on_event("startup")
async def startup():
    await init_db()