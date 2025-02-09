from sqlalchemy.ext.asyncio import AsyncSession

from repository.users import UserRepository
from schemas import UserCreate
from repository.models import User
from schemas import UserModel
from services.hash import get_password_hash
from logging import Logger
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    """
    Service layer for user-related operations.

    This class provides methods for user creation, retrieval, email confirmation, 
    and avatar management, interacting with the `UserRepository`.
    """

    def __init__(self, logger: Logger, db: AsyncSession):
        """
        Initialize a `UserService` instance.

        :param logger: Logger instance for logging user operations.
        :type logger: Logger

        :param db: AsyncSession for database operations.
        :type db: AsyncSession
        """
        self.__user_repository = UserRepository(db)
        self.__logger = logger

    async def create_user(self, body: UserCreate) -> UserModel:
        """
        Create a new user and store it in the database.

        :param body: The user data required for creation.
        :type body: UserCreate

        :return: The newly created user as a `UserModel`.
        :rtype: UserModel

        :raises SQLAlchemyError:
            If an error occurs during user creation.

        :example:
            >>> user_data = UserCreate(username="johndoe", email="john@example.com", password="securepass")
            >>> created_user = await user_service.create_user(user_data)
            >>> print(f"User created: {created_user.username}")
        """
        self.__logger.info(
            f"Creating user username: '{body.username}' email: '{body.email}'")
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=get_password_hash(body.password),
            avatar=None
        )
        found = await self.__user_repository.create_user(user)
        return self.__transform_user_model(found)

    async def get_user_by_username(self, username: str) -> UserModel | None:
        """
        Retrieve a user by their username.

        :param username: The username to search for.
        :type username: str

        :return: The user as `UserModel` if found, otherwise `None`.
        :rtype: UserModel | None

        :raises SQLAlchemyError:
            If an error occurs during the query.

        :example:
            >>> user = await user_service.get_user_by_username("johndoe")
            >>> if user:
            ...     print(f"User found: {user.username}")
        """
        found = await self.get_user_entity_by_username(username)
        return self.__transform_user_model(found)

    async def get_user_by_email(self, email: str) -> UserModel | None:
        """
        Retrieve a user by their email address.

        :param email: The email address to search for.
        :type email: str

        :return: The user as `UserModel` if found, otherwise `None`.
        :rtype: UserModel | None

        :raises SQLAlchemyError:
            If an error occurs during the query.

        :example:
            >>> user = await user_service.get_user_by_email("john@example.com")
            >>> if user:
            ...     print(f"User found: {user.email}")
        """
        found = await self.get_user_entity_by_email(email)
        return self.__transform_user_model(found)

    async def confirmed_email(self, email: str):
        """
        Confirm a user's email address.

        :param email: The email to be confirmed.
        :type email: str

        :raises SQLAlchemyError:
            If an error occurs while updating the user's email status.

        :example:
            >>> await user_service.confirmed_email("john@example.com")
        """
        self.__logger.debug(f"Confirming email: '{email}'")
        await self.__user_repository.confirmed_email(email)

    async def get_user_entity_by_username(self, username: str) -> User | None:
        """
        Retrieve a `User` entity by their username.

        :param username: The username to search for.
        :type username: str

        :return: The `User` object if found, otherwise `None`.
        :rtype: User | None

        :raises SQLAlchemyError:
            If an error occurs during the query.
        """
        self.__logger.debug(f"Get user by username: '{username}'")
        return await self.__user_repository.get_user_by_username(username)

    async def get_user_entity_by_email(self, email: str) -> User | None:
        """
        Retrieve a `User` entity by their email address.

        :param email: The email to search for.
        :type email: str

        :return: The `User` object if found, otherwise `None`.
        :rtype: User | None

        :raises SQLAlchemyError:
            If an error occurs during the query.
        """
        self.__logger.debug(f"Get user by email: '{email}'")
        return await self.__user_repository.get_user_by_email(email)

    async def update_avatar_url(self, username: str, url: str):
        """
        Update the avatar URL for a user.

        :param username: The username of the user whose avatar needs updating.
        :type username: str

        :param url: The new avatar URL.
        :type url: str

        :return: The updated `UserModel` object.
        :rtype: UserModel

        :raises SQLAlchemyError:
            If an error occurs while updating the avatar.

        :example:
            >>> updated_user = await user_service.update_avatar_url("johndoe", "https://avatar.url/image.jpg")
            >>> print(f"Updated avatar: {updated_user.avatar}")
        """
        self.__logger.debug(f"Update avatar for username: '{username}'")
        found = await self.get_user_entity_by_username(username)
        found.avatar = url
        await self.__user_repository.update(found)
        return self.__transform_user_model(found)

    def __transform_user_model(self, user: User) -> UserModel | None:
        return UserModel.model_validate(user) if user else None
