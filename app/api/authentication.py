from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from logger.logger import build_logger
from fastapi.security import OAuth2PasswordRequestForm
from services.hash import verify_password
from services.auth import create_access_token
from services.email import (
    send_confirmation_email,
    get_email_from_token,
    send_reset_password,
)
from pathlib import Path

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
    """
    Register a new user.

    This endpoint creates a new user account and sends an email confirmation request.

    :param background_tasks: Background task manager for sending the confirmation email.
    :type background_tasks: BackgroundTasks

    :param user_data: The user registration data.
    :type user_data: UserCreate

    :param request: The incoming request object.
    :type request: Request

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: The created user object.
    :rtype: UserModel

    :raises HTTPException:
        - 409 Conflict: If the username or email is already in use.
        - 422 Unprocessable Entity: If the request data is invalid.
        - 500 Internal Server Error: If an unexpected error occurs.
    """
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

    send_confirmation_email(
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
    """
    Authenticate a user and generate an access token.

    This endpoint verifies the user's credentials and returns a JWT token if authentication is successful.

    :param form_data: The login credentials submitted via form data.
    :type form_data: OAuth2PasswordRequestForm

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: A JWT access token.
    :rtype: TokenModel

    :raises HTTPException:
        - 401 Unauthorized: If the credentials are incorrect or the email is not confirmed.
    """
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
    """
    Confirm a user's email using a verification token.

    :param token: The email verification token.
    :type token: str

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: A confirmation response message.
    :rtype: ConfirmationResponse

    :raises HTTPException:
        - 400 Bad Request: If the verification fails.
        - 422 Unprocessable Entity: If the token is invalid.
    """
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
async def confirm_email(
    body: ConfirmationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a new email confirmation.

    This endpoint allows a user to request a new confirmation email if they haven't received one.

    :param body: The request body containing the user's email.
    :type body: ConfirmationRequest

    :param background_tasks: Background task manager for sending the confirmation email.
    :type background_tasks: BackgroundTasks

    :param request: The incoming request object.
    :type request: Request

    :param db: The database session dependency.
    :type db: AsyncSession

    :return: A confirmation response message.
    :rtype: ConfirmationResponse

    :raises HTTPException:
        - 400 Bad Request: If the email is unknown.
        - 422 Unprocessable Entity: If the request data is invalid.
    """
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
        send_confirmation_email(
            background_tasks, logger, user.email, user.username, request.base_url
        )
    return ConfirmationResponse(message=f"Please check your email for confirmation")


@router.post(
    "/reset_password",
    status_code=status.HTTP_201_CREATED,
    response_model=ConfirmationResponse,
    responses={
        400: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def reset_password(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates the password reset process by sending an email with a reset link.

    :param body: Request body containing the user's email.
    :type body: ResetPasswordRequest
    :param background_tasks: Background task manager to send emails asynchronously.
    :type background_tasks: BackgroundTasks
    :param request: The current request instance.
    :type request: Request
    :param db: The database session dependency.
    :type db: AsyncSession
    :return: A confirmation response message.
    :rtype: ConfirmationResponse
    """
    user_service = UserService(logger, db)
    user = await user_service.get_user_by_email(body.email)
    if user:
        send_reset_password(
            background_tasks, logger, user.email, user.username, request.base_url
        )
    return ConfirmationResponse(message="Please check your email for reset password")


@router.get("/reseted_password/{token}", response_class=HTMLResponse)
async def get_reseted_password(
    token: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Serves the password reset page where users can enter a new password.

    :param token: The password reset token.
    :type token: str
    :param request: The current request instance.
    :type request: Request
    :param db: The database session dependency.
    :type db: AsyncSession
    :return: An HTML response rendering the reset password page.
    :rtype: HTMLResponse
    """

    email = get_email_from_token(token)
    user_service = UserService(logger, db)
    user = await user_service.get_user_entity_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    templates = Jinja2Templates(directory=Path(
        __file__).parent.parent / "templates")
    return templates.TemplateResponse(
        "reset_password_page.html",
        {
            "request": request,
            "token": token,
            "host": request.base_url,
            "username": user.username,
        },
    )


@router.post(
    "/reseted_password",
    status_code=status.HTTP_201_CREATED,
    response_model=ConfirmationResponse,
    responses={
        400: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def perform_reseted_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Processes the password reset by updating the user's password.

    :param body: Request body containing the reset token and new password.
    :type body: ChangePasswordRequest
    :param db: The database session dependency.
    :type db: AsyncSession
    :return: A confirmation response message indicating success.
    :rtype: ConfirmationResponse
    """
    email = get_email_from_token(body.token)
    user_service = UserService(logger, db)
    user = await user_service.get_user_entity_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    await user_service.update_password(user.username, body.password)
    return ConfirmationResponse(
        message=f"The password for {user.username} has been updated"
    )
