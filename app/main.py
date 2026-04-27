import logging
from fastapi import FastAPI
from app.routes import auth
from app.db.session import init_db


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
app = FastAPI()
app.include_router(auth.router)

@app.on_event("startup")
async def startup():
    await init_db()