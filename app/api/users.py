from fastapi import APIRouter, Depends, Request, UploadFile, File 
from schemas import UserModel, ErrorsContent
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.auth import get_current_user, get_current_admin_user
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
    """
    Retrieve the authenticated user's profile.

    This endpoint returns the details of the currently logged-in user.

    :param request: The incoming request object.
    :type request: Request

    :param current_user: The currently authenticated user.
    :type current_user: UserModel

    :return: The authenticated user's profile.
    :rtype: UserModel

    :raises HTTPException:
        - 401 Unauthorized: If authentication fails.
        - 429 Too Many Requests: If rate limit is exceeded.
        - 500 Internal Server Error: If an unexpected error occurs.

    :example:
        >>> user = await login_user(request, current_user)
        >>> print(user.username)
    """
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
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the user's avatar.

    This endpoint allows an authenticated user to upload a new profile avatar.
    The image is stored in a cloud storage service, and the user's profile 
    is updated with the new avatar URL.

    :param file: The uploaded avatar file.
    :type file: UploadFile

    :param current_user: The currently authenticated user.
    :type current_user: UserModel

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: The updated user profile with the new avatar.
    :rtype: UserModel

    :raises HTTPException:
        - 401 Unauthorized: If authentication fails.
        - 429 Too Many Requests: If rate limit is exceeded.
        - 500 Internal Server Error: If an unexpected error occurs.

    :example:
        >>> updated_user = await update_avatar_user(file, current_user, db)
        >>> print(updated_user.avatar)
    """
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, current_user.username)

    user_service = UserService(logger, db)
    user = await user_service.update_avatar_url(current_user.username, avatar_url)

    return user
