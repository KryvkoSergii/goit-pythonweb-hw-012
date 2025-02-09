from conf.config import settings
import redis.asyncio as aioredis

import redis.asyncio as aioredis

async def get_redis():
    redis_conn = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis_conn
    finally:
        await redis_conn.close()