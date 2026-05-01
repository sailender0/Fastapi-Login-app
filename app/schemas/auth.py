from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):    
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr # This will now work once email-validator is installed
    password: str = Field(min_length=8)
    

class UserLogin(BaseModel):     
    username: str
    password: str

class UserPublic(BaseModel):    
    id: int
    username: str
    role: str
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    

class RefreshRequest(BaseModel):
    refresh_token: str