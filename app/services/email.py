from pathlib import Path
from fastapi import BackgroundTasks, HTTPException, status
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from logging import Logger
from conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates",
)


def send_confirmation_email(
    background_tasks: BackgroundTasks,
    logger: Logger,
    email: str,
    username: str,
    host: str
):
    """
    Send a confirmation email asynchronously.

    This function generates an email verification token and schedules an 
    email to be sent in the background using FastMail.

    :param background_tasks: FastAPI background task manager.
    :type background_tasks: BackgroundTasks

    :param logger: Logger instance for logging email events.
    :type logger: Logger

    :param email: The recipient's email address.
    :type email: str

    :param username: The recipient's username.
    :type username: str

    :param host: The server's hostname for generating the verification link.
    :type host: str

    :raises FastMailError:
        If there is an issue while sending the email.

    :example:
        >>> send_email(background_tasks, logger, "user@example.com", "username", "https://example.com")
    """
    token_verification = create_email_token({"sub": email})
    message = MessageSchema(
        subject="Confirm your email",
        recipients=[email],
        template_body={
            "host": host,
            "username": username,
            "token": token_verification,
        },
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message, message, template_name="verify_email.html"
    )
    logger.debug(
        f"Confirmation email for {email} has been placed to the queue")


def create_email_token(data: dict) -> str:
    """
    Generate an email verification token.

    This function encodes a dictionary into a JWT token with a validity 
    period of 7 days.

    :param data: The payload containing user email for encoding.
    :type data: dict

    :return: The generated JWT token as a string.
    :rtype: str

    :raises JWTError:
        If an error occurs during token generation.

    :example:
        >>> token = create_email_token({"sub": "user@example.com"})
        >>> print(token)
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET,
                       algorithm=settings.JWT_ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Decode an email verification token.

    This function extracts the email address from a given JWT token.

    :param token: The JWT token containing the email address.
    :type token: str

    :return: The extracted email address.
    :rtype: str

    :raises HTTPException:
        If the token is invalid or expired.

    :example:
        >>> email = get_email_from_token(token)
        >>> print(email)  # Output: user@example.com
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect verification token",
        )
    
def send_reset_password(
    background_tasks: BackgroundTasks,
    logger: Logger,
    email: str,
    username: str,
    host: str
):
    """
    Sends a password reset email asynchronously using FastMail.
    
    :param background_tasks: Background task manager to send emails asynchronously.
    :type background_tasks: BackgroundTasks
    :param logger: Logger instance for logging email operations.
    :type logger: Logger
    :param email: The recipient's email address.
    :type email: str
    :param username: The username of the recipient.
    :type username: str
    :param host: The host URL for generating the password reset link.
    :type host: str
    """
    token_verification = create_email_token({"sub": email})
    message = MessageSchema(
        subject="Reset password",
        recipients=[email],
        template_body={
            "host": host,
            "username": username,
            "token": token_verification,
        },
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message, message, template_name="reset_password_email.html"
    )
    logger.debug(
        f"Reset password for {email} has been placed to the queue"
    )
