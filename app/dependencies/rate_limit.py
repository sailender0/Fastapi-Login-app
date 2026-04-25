from fastapi import Request, HTTPException, status, Depends
from app.services.rate_limiter import check_rate_limit


async def rate_limit_dependency(request: Request):
    ip = request.client.host
    form = await request.form()
    username = form.get("username", "anonymous")
    # username = "anonymous"
    allowed,retry_after= await check_rate_limit(ip, username)
    return {
        "allowed": allowed,
        "retry_after": retry_after,
        "username": username,
        "ip": ip
    }