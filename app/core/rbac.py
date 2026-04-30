from fastapi import Request, HTTPException, Depends
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

def require_roles(*allowed_roles):
    async def checker(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        role = request.cookies.get("session_role")
        user = request.cookies.get("session_user")

        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return {"username": user, "role": role}

    return checker