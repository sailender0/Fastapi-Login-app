from sqlalchemy import Column, Integer, String
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    token_version = Column(Integer, default=0)
    role = Column(String, default="user")

