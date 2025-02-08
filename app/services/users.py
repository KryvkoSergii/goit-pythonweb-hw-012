from sqlalchemy.ext.asyncio import AsyncSession

from repository.users import UserRepository
from schemas import UserCreate
from repository.models import User
from schemas import UserModel
from services.hash import get_password_hash
from logging import Logger
import cloudinary


class UserService:

    def __init__(self, logger: Logger, db: AsyncSession):
        self.__user_repository = UserRepository(db)
        self.__logger = logger

    async def create_user(self, body: UserCreate) -> UserModel:
        self.__logger.info(f"Creating user username: '{body.username}' email: '{body.email}'")
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=get_password_hash(body.password),
            avatar=None
        )
        found = await self.__user_repository.create_user(user)
        return self.__transform_user_model(found)

    async def get_user_by_username(self, username: str) -> UserModel | None:
        found = await self.get_user_entity_by_username(username)
        return self.__transform_user_model(found)

    async def get_user_by_email(self, email: str) -> UserModel | None:
        found = await self.get_user_entity_by_email(email)
        return self.__transform_user_model(found)
    
    async def confirmed_email(self, email: str):
        self.__logger.debug(f"Confirmating email: '{email}'")
        await self.__user_repository.confirmed_email(email)
    
    async def get_user_entity_by_username(self, username: str) -> User | None:
        self.__logger.debug(f"Get user by username: '{username}'")
        return await self.__user_repository.get_user_by_username(username)
    
    async def get_user_entity_by_email(self, email: str) -> User | None:
        self.__logger.debug(f"Get user by email: '{email}'")
        return await self.__user_repository.get_user_by_email(email)
    
    async def update_avatar_url(self, username: str, url: str):
        self.__logger.debug(f"Update avatar for username: '{username}'")
        found = await self.get_user_entity_by_username(username)
        found.avatar = url
        await self.__user_repository.update(found)
        return self.__transform_user_model(found)

    def __transform_user_model(self, user: User) -> UserModel | None:
        return UserModel.model_validate(user) if user else None
        
