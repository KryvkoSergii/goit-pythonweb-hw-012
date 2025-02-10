from conf.config import settings 
import redis.asyncio as aioredis

async def get_redis():
    """
    Asynchronously retrieves a Redis connection from the configured Redis URL.
    
    This function establishes a connection to Redis using the `settings.REDIS_URL`
    and ensures that the connection is properly closed when done.
    
    :yield: An asynchronous Redis connection instance.
    :rtype: aioredis.Redis
    """
    redis_conn = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis_conn
    finally:
        await redis_conn.close()