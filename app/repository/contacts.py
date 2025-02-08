from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repository.models import Contact
from typing import List
from schemas import ContactsQuery
from sqlalchemy import select, func


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list_by_query(self, query: ContactsQuery) -> List[Contact]:
        dynamic_query = select(Contact)
        if query.first_name:
            dynamic_query = dynamic_query.where(
                func.upper(Contact.first_name) == query.first_name.upper()
            )
        if query.last_name:
            dynamic_query = dynamic_query.where(
                func.upper(Contact.last_name) == query.last_name.upper()
            )
        if query.email:
            dynamic_query = dynamic_query.where(
                func.upper(Contact.email) == query.email.upper()
            )
        if query.date_from:
            dynamic_query = dynamic_query.where(Contact.date >= query.date_from)
        if query.date_to:
            dynamic_query = dynamic_query.where(Contact.date <= query.date_to)
        dynamic_query = dynamic_query.where(Contact.user_id == query.user_id)
        if query.skip:
            dynamic_query = dynamic_query.offset(query.skip)
        if query.limit:
            dynamic_query = dynamic_query.limit(query.limit)
        contacts = await self.session.execute(dynamic_query)
        return contacts.scalars().all()

    async def get_by_id(self, id: int, user_id: int) -> Contact | None:
        stmt = select(Contact).filter_by(id=id, user_id=user_id)
        contact = await self.session.execute(stmt)
        return contact.scalar_one_or_none()

    async def create(self, contact: Contact) -> Contact:
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return await self.get_by_id(contact.id, contact.user_id)

    async def update(self, contact: Contact) -> Contact:
        await self.session.commit()
        await self.session.refresh(contact)
        return await self.get_by_id(contact.id, contact.user_id)

    async def remove(self, contact: Contact) -> Contact:
        await self.session.delete(contact)
        await self.session.commit()
        return contact
