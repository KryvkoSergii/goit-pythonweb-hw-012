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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unable to verify credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
logger = build_logger("auth", "DEBUG")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_SECONDS))
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserModel:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        iat: int = payload.get("iat")
        exp: int = payload.get("exp")
        now = time.time()

        if iat > now or now > exp:
            HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    service = UserService(logger, db)
    user = await service.get_user_by_username(username)

    if user is None:
        raise credentials_exception

    return user

