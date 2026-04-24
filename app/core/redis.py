import redis.asyncio as redis

# adjust host/port if using Docker or a remote Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,  # returns str instead of bytes
)