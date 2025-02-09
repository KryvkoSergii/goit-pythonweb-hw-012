from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, UTC
import time
from typing import Optional
from jose import JWTError, jwt
from conf.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, status, HTTPException
from database.db import get_db
from services.users import UserService
from logger.logger import build_logger
from schemas import UserModel
from redis import Redis
from database.cache import get_redis
from services.cache import CacheService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unable to verify credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
logger = build_logger("auth", "DEBUG")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a JWT access token.

    This function encodes a given dictionary into a JWT token, setting 
    an expiration time based on the provided `expires_delta` or the 
    default expiration time from the application settings.

    :param data: The payload to encode into the token.
    :type data: dict

    :param expires_delta: The time delta until the token expires.
    :type expires_delta: Optional[timedelta]

    :return: The generated JWT token as a string.
    :rtype: str

    :raises JWTError:
        If an error occurs during token generation.

    :example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> print(token)
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + \
        (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_SECONDS))
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db),
    cache_db: Redis = Depends(get_redis)
) -> UserModel:
    """
    Retrieve the current authenticated user from a JWT token.

    This function decodes the provided JWT token to extract the username,
    validates the token's issue and expiration times, and fetches the user
    from the database.

    :param token: The JWT access token provided in the request.
    :type token: str

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: The authenticated user as a `UserModel`.
    :rtype: UserModel

    :raises HTTPException:
        - 401 Unauthorized: If the token is invalid or expired.
        - 401 Unauthorized: If the user is not found in the database.

    :example:
        >>> user = await get_current_user(token, db)
        >>> print(f"Authenticated user: {user.username}")
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )

    except JWTError:
        raise credentials_exception

    iat: int = payload.get("iat")
    exp: int = payload.get("exp")
    now = time.time()

    if iat > now or now > exp:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    cache = CacheService(logger, cache_db)
    user = await cache.get_user(token=token)

    if not user:
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        service = UserService(logger, db)
        user = await service.get_user_by_username(username)
        
        if user is None:
            raise credentials_exception
        
        await cache.set_user(token, user, exp)

    return user
