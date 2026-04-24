from app.core.redis import redis_client
from typing import Tuple

# Config
MAX_ATTEMPTS = 5
BASE_LOCK_SECONDS = 300  # 5 minutes
WINDOW_SECONDS = 300     # sliding window TTL

def _key(ip: str, username: str) -> str:
    # per-IP + username to reduce credential stuffing impact
    return f"login:{ip}:{username}"

async def check_rate_limit(ip: str, username: str) -> Tuple[bool, int]:
    """
    Returns:
        allowed: bool
        retry_after_seconds: int (0 if allowed)
    """
    key = _key(ip, username)
    attempts = await redis_client.get(key)

    if attempts and int(attempts) >= MAX_ATTEMPTS:
        ttl = await redis_client.ttl(key)
        return False, max(ttl, 0)

    return True, 0


async def register_failure(ip: str, username: str) -> int:
    
    key = _key(ip, username)

    # atomic increment
    attempts = await redis_client.incr(key)

    # set/refresh TTL (sliding window)
    await redis_client.expire(key, WINDOW_SECONDS)

    return attempts


async def register_success(ip: str, username: str):
    """
    Clears attempts after successful login.
    """
    key = _key(ip, username)
    await redis_client.delete(key)