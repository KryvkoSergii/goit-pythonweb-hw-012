import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.repository.users import UserRepository
from app.repository.models import Contact, User, Base
from datetime import datetime, timedelta
import pytest_asyncio

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture()
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def user_repo(db_session: AsyncSession):
    return UserRepository(db_session)


@pytest_asyncio.fixture()
async def predefined_user(db_session: AsyncSession):
    user = User(
        username="user",
        email="user@gmail.com",
        hashed_password="hash",
        created_at=datetime.now(),
        confirmed=True,
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def predefined_admin(db_session: AsyncSession):
    admin = User(
        username="admin",
        email="admin@gmail.com",
        hashed_password="hash",
        created_at=datetime.now(),
        confirmed=True,
        role="user",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository, predefined_admin: User):
    now = datetime.now()
    user = User(
        username="user",
        email="user@gmail.com",
        hashed_password="hash",
        created_at=now,
        confirmed=True,
        role="user",
    )
    created: User = await user_repo.create_user(user)

    assert created.username == "user"
    assert created.email == "user@gmail.com"
    assert created.hashed_password == "hash"
    assert created.created_at == now
    assert created.confirmed == True
    assert created.role == "user"


@pytest.mark.asyncio
async def test_get_user_by_username(
    user_repo: UserRepository, predefined_user: User, predefined_admin: User
):
    found: User = await user_repo.get_user_by_username(predefined_user.username)
    assert found.id == predefined_user.id


@pytest.mark.asyncio
async def test_get_user_by_email(
    user_repo: UserRepository, predefined_user: User, predefined_admin: User
):
    found: User = await user_repo.get_user_by_email(predefined_user.email)
    assert found.id == predefined_user.id


@pytest.mark.asyncio
async def test_confirmed_email(user_repo: UserRepository):
    now = datetime.now()
    user = User(
        username="user",
        email="user@gmail.com",
        hashed_password="hash",
        created_at=now,
        confirmed=False,
        role="user",
    )
    created: User = await user_repo.create_user(user)

    await user_repo.confirmed_email(created.email)

    found: User = await user_repo.get_user_by_email(created.email)
    assert found.id == created.id


@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepository):
    now = datetime.now()
    user = User(
        username="user",
        email="user@gmail.com",
        hashed_password="hash",
        created_at=now,
        confirmed=False,
        role="user",
    )
    user = await user_repo.create_user(user)

    found: User = await user_repo.get_user_by_email(user.email)
    found.username = "my-user"
    found.email = "my-user@gmail.com"
    found.hashed_password = "new-hash"
    found.confirmed = False
    found.role = "admin"

    await user_repo.update(found)
    updated: User = await user_repo.get_user_by_email(found.email)

    assert updated.id == user.id
    assert updated.username == "my-user"
    assert updated.email == "my-user@gmail.com"
    assert updated.hashed_password == "new-hash"
    assert updated.confirmed == False
    assert updated.role == "admin"
