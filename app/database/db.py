import contextlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from conf.config import settings


class DatabaseSessionManager:
    """
    Manages database connections and sessions.

    This class provides a session manager for handling database transactions 
    using SQLAlchemy's asynchronous capabilities.
    """

    def __init__(self, url: str):
        """
        Initialize the database session manager.

        :param url: The database connection URL.
        :type url: str
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provide an asynchronous database session.

        This method initializes a new session, ensures rollback on exceptions, 
        and closes the session once it is no longer needed.

        :yield: An asynchronous database session.
        :rtype: AsyncSession

        :raises Exception:
            If the session manager is not properly initialized.

        :raises SQLAlchemyError:
            If an error occurs during database transactions.

        :example:
            >>> async with sessionmanager.session() as session:
            ...     result = await session.execute(query)
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Dependency function for retrieving a database session.

    This function is designed for use in FastAPI dependency injection,
    ensuring that each request gets a fresh database session.

    :yield: An asynchronous database session.
    :rtype: AsyncSession

    :example:
        >>> async def some_endpoint(db: AsyncSession = Depends(get_db)):
        ...     result = await db.execute(query)
    """
    async with sessionmanager.session() as session:
        yield session
