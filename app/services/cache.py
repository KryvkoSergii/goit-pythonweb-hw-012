import redis
import json
from schemas import UserModel
from logging import Logger

class CacheService:

    def __init__(self, logger: Logger, redis_connection: redis.Redis):
        self.redis_connection = redis_connection
        self.logger = logger

    async def get_user(self, token: str) -> UserModel | None:
        self.logger.debug(f"get user from cache")
        user_json = await self.redis_connection.get(token)
        if user_json:
            user = UserModel(**json.loads(user_json))
            self.logger.debug(f"got user '{user.username}' from cache")
            return user
        else:
            self.logger.debug(f"no user found in cache")
            return None

    async def set_user(self, token: str, user: UserModel, evict: int):
        serialized = user.model_dump()
        serialized = json.dumps(serialized)
        self.logger.debug(f"set user '{user.username}' to cache. Expiration is: {evict} object: {serialized}")
        await self.redis_connection.set(token,serialized, exat=evict)

    async def remove_user(self, token: str):
        self.logger.debug(f"remove cache by token")
        self.redis_connection.delete(token)