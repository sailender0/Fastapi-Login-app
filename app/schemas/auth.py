from pydantic import BaseModel

class UserCreate(BaseModel):    
    username: str
    password: str

class UserLogin(BaseModel):     
    username: str
    password: str

class UserPublic(BaseModel):    
    id: int
    username: str
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
