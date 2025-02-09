import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.repository.contacts import ContactRepository
from app.repository.models import Contact
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def contact_repo(db_session: AsyncSession):
    return ContactRepository(db_session)

@pytest.mark.asyncio
async def test_create_contact(contact_repo):
    contact = Contact(name="John Doe", email="john.doe@example.com")
    created_contact = await contact_repo.create(contact)
    
    assert created_contact.id is not None
    assert created_contact.name == "John Doe"
    assert created_contact.email == "john.doe@example.com"

@pytest.mark.asyncio
async def test_get_contact(contact_repo):
    contact = Contact(name="Jane Doe", email="jane.doe@example.com")
    created_contact = await contact_repo.create(contact)
    fetched_contact = await contact_repo.get(created_contact.id)
    
    assert fetched_contact is not None
    assert fetched_contact.id == created_contact.id

@pytest.mark.asyncio
async def test_delete_contact(contact_repo):
    contact = Contact(name="Alice", email="alice@example.com")
    created_contact = await contact_repo.create(contact)
    
    await contact_repo.delete(created_contact.id)
    fetched_contact = await contact_repo.get(created_contact.id)
    assert fetched_contact is None