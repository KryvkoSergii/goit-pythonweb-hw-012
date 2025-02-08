from fastapi import APIRouter, Depends, Request, UploadFile, File
from schemas import UserModel, ErrorsContent
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.auth import get_current_user
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from conf.config import settings
from services.users import UserService
from logger.logger import build_logger
from services.upload_file import UploadFileService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)
logger = build_logger("users", "DEBUG")


@router.get(
    "/me",
    response_model=UserModel,
    responses={
        401: {"model": ErrorsContent},
        429: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
@limiter.limit("5/minute")
async def login_user(
    request: Request, current_user: UserModel = Depends(get_current_user)
):
    return current_user


@router.patch(
    "/avatar",
    response_model=UserModel,
    responses={
        401: {"model": ErrorsContent},
        429: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, current_user.username)

    user_service = UserService(logger, db)
    user = await user_service.update_avatar_url(current_user.username, avatar_url)

    return user
