from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repository.models import User


class UserRepository:
    """
    Repository class for handling database operations related to the User model.

    This class provides methods to create, retrieve, update, and confirm users 
    in an asynchronous database session.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize a UserRepository instance.

        :param session: An AsyncSession object connected to the database.
        :type session: AsyncSession
        """
        self.db = session

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        :param username: The username of the user to retrieve.
        :type username: str

        :return: The `User` object if found, otherwise `None`.
        :rtype: User | None

        :raises SQLAlchemyError:
            If an error occurs while querying the database.

        :example:
            >>> user = await repository.get_user_by_username("john_doe")
            >>> if user:
            ...     print(f"User found: {user.username}")
            ... else:
            ...     print("User not found.")
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        :param email: The email of the user to retrieve.
        :type email: str

        :return: The `User` object if found, otherwise `None`.
        :rtype: User | None

        :raises SQLAlchemyError:
            If an error occurs while querying the database.

        :example:
            >>> user = await repository.get_user_by_email("john@example.com")
            >>> if user:
            ...     print(f"User found: {user.email}")
            ... else:
            ...     print("User not found.")
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        """
        Create a new user and persist it in the database.

        :param user: The `User` object to be created.
        :type user: User

        :return: The newly created `User` object.
        :rtype: User

        :raises SQLAlchemyError:
            If an error occurs while committing the transaction.

        :example:
            >>> new_user = User(username="jane_doe", email="jane@example.com")
            >>> created_user = await repository.create_user(new_user)
            >>> print(f"Created user: {created_user.username}")
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirm a user's email by setting the `confirmed` attribute to True.

        :param email: The email address of the user whose email should be confirmed.
        :type email: str

        :raises SQLAlchemyError:
            If an error occurs while committing the transaction.

        :example:
            >>> await repository.confirmed_email("john@example.com")
            >>> user = await repository.get_user_by_email("john@example.com")
            >>> print(f"Email confirmed: {user.confirmed}")
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update(self, user: User) -> User:
        """
        Update an existing user's information in the database.

        :param user: The `User` object with updated attributes.
        :type user: User

        :return: The updated `User` object.
        :rtype: User

        :raises SQLAlchemyError:
            If an error occurs while committing the transaction.

        :example:
            >>> user.username = "new_username"
            >>> updated_user = await repository.update(user)
            >>> print(f"Updated username: {updated_user.username}")
        """
        await self.db.commit()
        await self.db.refresh(user)
        return user
