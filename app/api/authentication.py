from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks, Request
from services.users import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from schemas import (
    UserCreate,
    UserModel,
    TokenModel,
    ErrorsContent,
    ConfirmationResponse,
    ConfirmationRequest,
)
from logger.logger import build_logger
from fastapi.security import OAuth2PasswordRequestForm
from services.hash import verify_password
from services.auth import create_access_token
from services.email import send_email, get_email_from_token


logger = build_logger("auth", "DEBUG")
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def register_user(
    background_tasks: BackgroundTasks,
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(logger, db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such email already exists",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with such username already exists",
        )

    new_user = await user_service.create_user(user_data)

    send_email(
        background_tasks, logger, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post(
    "/login",
    response_model=TokenModel,
    responses={
        401: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user_service = UserService(logger, db)
    user = await user_service.get_user_entity_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not confirmed",
        )
    return TokenModel(access_token=create_access_token(data={"sub": user.username}))


@router.get(
    "/confirmed_email/{token}",
    status_code=status.HTTP_201_CREATED,
    response_model=ConfirmationResponse,
    responses={
        400: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    email = get_email_from_token(token)
    user_service = UserService(logger, db)
    user = await user_service.get_user_entity_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return ConfirmationResponse(message=f"The email {email} is already confirmed")
    await user_service.confirmed_email(email)
    return ConfirmationResponse(message=f"The email {email} has been confirmed")


@router.post(
    "/confirm_email",
    status_code=status.HTTP_201_CREATED,
    response_model=ConfirmationResponse,
    responses={
        400: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def request_email(
    body: ConfirmationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(logger, db)
    user = await user_service.get_user_entity_by_email(body.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown email"
        )

    if user.confirmed:
        return ConfirmationResponse(
            message=f"The email {body.email} is already confirmed"
        )
    if user:
        send_email(
            background_tasks, logger, user.email, user.username, request.base_url
        )
    return ConfirmationResponse(message=f"Please check your email for confirmation")
