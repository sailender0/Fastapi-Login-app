from typing import Optional

from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):    
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr 
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
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None

# What we send back to the user
class ProfileRead(BaseModel):
    username: str
    email: Optional[EmailStr]
    full_name: Optional[str]
    bio: Optional[str]
    profile_image: Optional[str]

    class Config:
        from_attributes = True