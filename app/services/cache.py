import redis 
import json
from schemas import UserModel
from logging import Logger

class CacheService:
    """
    A service for caching user data using Redis.
    
    :param logger: Logger instance for logging cache operations.
    :type logger: Logger
    :param redis_connection: Redis connection instance.
    :type redis_connection: redis.Redis
    """

    def __init__(self, logger: Logger, redis_connection: redis.Redis):
        """
        Initializes the CacheService with a logger and Redis connection.
        
        :param logger: Logger instance.
        :type logger: Logger
        :param redis_connection: Redis connection instance.
        :type redis_connection: redis.Redis
        """
        self.redis_connection = redis_connection
        self.logger = logger

    async def get_user(self, token: str) -> UserModel | None:
        """
        Retrieves a user from the cache using a given token.
        
        :param token: The token associated with the cached user.
        :type token: str
        :return: The user if found, otherwise None.
        :rtype: UserModel | None
        """
        self.logger.debug("get user from cache")
        user_json = await self.redis_connection.get(token)
        if user_json:
            user = UserModel(**json.loads(user_json))
            self.logger.debug(f"got user '{user.username}' from cache")
            return user
        else:
            self.logger.debug("no user found in cache")
            return None

    async def set_user(self, token: str, user: UserModel, evict: int):
        """
        Stores a user in the cache with a specified expiration time.
        
        :param token: The token associated with the user.
        :type token: str
        :param user: The user data to be cached.
        :type user: UserModel
        :param evict: The expiration time for the cache entry in seconds.
        :type evict: int
        """
        serialized = user.model_dump()
        serialized = json.dumps(serialized)
        self.logger.debug(f"set user '{user.username}' to cache. Expiration is: {evict} object: {serialized}")
        await self.redis_connection.set(token, serialized, exat=evict)

    async def remove_user(self, token: str):
        """
        Removes a user from the cache by token.
        
        :param token: The token associated with the cached user.
        :type token: str
        """
        self.logger.debug("remove cache by token")
        self.redis_connection.delete(token)
