from fastapi import Request, HTTPException, status, Depends
from app.services.rate_limiter import check_rate_limit


async def rate_limit_dependency(request: Request):
    ip = request.client.host
    username = "anonymous"
    allowed = await check_rate_limit(ip, username)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later."
        )