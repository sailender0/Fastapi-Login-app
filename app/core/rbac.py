from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user 
from app.db.models import User

def require_roles(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions to access this resource"
            )
        return current_user
    
    return role_checker