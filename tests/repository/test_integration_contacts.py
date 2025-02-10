import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.repository.contacts import ContactRepository
from app.repository.models import Contact, User, Base
from datetime import datetime, timedelta
import pytest_asyncio
from app.schemas import ContactsQuery

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
async def contact_repo(db_session: AsyncSession):
    return ContactRepository(db_session)


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
async def test_create_contact(
    contact_repo: ContactRepository, predefined_user: User, predefined_admin: User
):
    now = datetime.now()
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        date=now,
        notes="notes",
        user_id=predefined_user.id,
    )
    created_contact = await contact_repo.create(contact)

    assert created_contact.id is not None
    assert created_contact.first_name == "John"
    assert created_contact.last_name == "Doe"
    assert created_contact.email == "john.doe@example.com"
    assert created_contact.phone == "1234567890"
    assert datetime.now() - now < timedelta(seconds=30)
    assert created_contact.notes == "notes"
    assert created_contact.user_id == predefined_user.id


@pytest.mark.asyncio
async def test_get_contact_by_id(
    contact_repo: ContactRepository, predefined_user: User
):
    now = datetime.now()
    contact_1 = build_contact(predefined_user, now)
    contact_1 = await contact_repo.create(contact_1)
    contact_2 = build_contact(predefined_user, now)
    contact_2 = await contact_repo.create(contact_2)

    fetched_contact = await contact_repo.get_by_id(contact_2.id, predefined_user.id)

    assert fetched_contact is not None
    assert fetched_contact.id == contact_2.id


def build_contact(predefined_user, now):
    return Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        date=now,
        notes="notes",
        user_id=predefined_user.id,
    )


@pytest.mark.asyncio
async def test_delete_contact(contact_repo: ContactRepository, predefined_user: User):
    now = datetime.now()
    contact_1 = build_contact(predefined_user, now)
    contact_1 = await contact_repo.create(contact_1)

    await contact_repo.remove(contact_1)
    fetched_contact = await contact_repo.get_by_id(contact_1.id, predefined_user.id)
    assert fetched_contact is None


async def serch_query_params():
    return [
        ContactsQuery(first_name="Sarah", skip=0, limit=10),
        ContactsQuery(last_name="Dow", skip=0, limit=10),
        ContactsQuery(email="sarah.dow@example.com", skip=0, limit=10),
        ContactsQuery(
            date_from=datetime.now().date() + timedelta(days=1),
            date_to=datetime.now().date() + timedelta(days=4),
            skip=0,
            limit=10,
        ),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", asyncio.run(serch_query_params()))
async def test_search_contact_by_criteria(
    contact_repo: ContactRepository,
    predefined_user: User,
    predefined_admin: User,
    query: ContactsQuery,
):
    now = datetime.now()
    contact_1 = build_contact(predefined_user, now)
    contact_1 = await contact_repo.create(contact_1)
    contact_2 = build_contact(predefined_admin, now)
    contact_2 = await contact_repo.create(contact_2)
    contact_3 = Contact(
        first_name="Sarah",
        last_name="Dow",
        email="sarah.dow@example.com",
        phone="00000000",
        date=now + timedelta(days=3),
        notes="her notes",
        user_id=predefined_admin.id,
    )
    contact_3 = await contact_repo.create(contact_3)

    query.user_id = predefined_admin.id
    fetched_contact = await contact_repo.get_list_by_query(query)

    assert len(fetched_contact) == 1
    assert fetched_contact[0] is not None
    assert fetched_contact[0].id == contact_3.id


@pytest.mark.asyncio
async def test_update_contact(
    contact_repo: ContactRepository, predefined_user: User, predefined_admin: User
):
    now = datetime.now()
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        date=now,
        notes="notes",
        user_id=predefined_user.id,
    )
    created_contact = await contact_repo.create(contact)

    fetched_contact = await contact_repo.get_by_id(
        created_contact.id, predefined_user.id
    )

    fetched_contact.first_name = "Sarah"
    fetched_contact.last_name = "Dow"
    fetched_contact.email = "sarah.dow@example.com"
    fetched_contact.phone = "00000000"
    fetched_contact.notes = "her notes"
    fetched_contact.user_id = predefined_admin.id

    await contact_repo.update(fetched_contact)

    fetched_contact = await contact_repo.get_by_id(
        created_contact.id, predefined_admin.id
    )

    assert fetched_contact.id == created_contact.id
    assert fetched_contact.first_name == "Sarah"
    assert fetched_contact.last_name == "Dow"
    assert fetched_contact.email == "sarah.dow@example.com"
    assert fetched_contact.phone == "00000000"
    assert fetched_contact.notes == "her notes"
    assert fetched_contact.user_id == predefined_admin.id
