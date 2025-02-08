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


def send_email(
    background_tasks: BackgroundTasks, 
    logger: Logger, 
    email: str, username: str, host: str
):
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
    logger.debug(f"Confirmation email for {email} has been placed to the queue")


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def get_email_from_token(token: str):
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