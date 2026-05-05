from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user 
from app.db.models import User
import logging

logging.basicConfig(level=logging.INFO)

def require_roles(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        logging.info(f"Checking roles for user: {current_user.username} (Role: {current_user.role})")
        if current_user.role not in allowed_roles:
            logging.warning(f"Access Denied: User {current_user.username} with role {current_user.role} tried to access admin route.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions to access this resource"
            )
        return current_user
    
    return role_checker