from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repository.models import Contact
from typing import List
from schemas import ContactsQuery
from sqlalchemy import select, func


class ContactRepository:
    """
    Repository class for handling database operations related to the Contact model.

    This class provides methods to create, search, update, and remove contacts for user 
    in an asynchronous database session.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize a ContactRepository instance.

        :param session: An AsyncSession object connected to the database.
        :type session: AsyncSession
        """
        self.session = session

    async def get_list_by_query(self, query: ContactsQuery) -> List[Contact]:
        """
        Retrieve a list of contacts based on the specified query parameters.

        This method constructs a dynamic SQL query using SQLAlchemy to filter contacts
        based on the provided query attributes, such as first name, last name, email,
        date range, user ID, pagination (skip, limit), and case-insensitive matching.

        :param query:
            An instance of `ContactsQuery` containing filter criteria such as
            `first_name`, `last_name`, `email`, `date_from`, `date_to`, `user_id`,
            `skip`, and `limit`.

        :type query: ContactsQuery

        :return:
            A list of `Contact` objects that match the query criteria.

        :rtype: List[Contact]

        :raises SQLAlchemyError:
            If there is an issue executing the query in the database session.

        :example:
            >>> query = ContactsQuery(first_name="John", email="john.doe@example.com")
            >>> contacts = await repository.get_list_by_query(query)
            >>> print(contacts)

        """
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
            dynamic_query = dynamic_query.where(
                Contact.date >= query.date_from)
        if query.date_to:
            dynamic_query = dynamic_query.where(
                Contact.date <= query.date_to)
        dynamic_query = dynamic_query.where(
            Contact.user_id == query.user_id)
        if query.skip:
            dynamic_query = dynamic_query.offset(query.skip)
        if query.limit:
            dynamic_query = dynamic_query.limit(query.limit)
        contacts = await self.session.execute(dynamic_query)
        return contacts.scalars().all()

    async def get_by_id(self, id: int, user_id: int) -> Contact | None:
        """
        Retrieve a contact by its unique identifier and user ID.

        This method queries the database to find a specific contact that matches
        the given `id` and `user_id`. If a matching contact is found, it is returned;
        otherwise, `None` is returned.

        :param id: 
            The unique identifier of the contact to retrieve.
        :type id: int

        :param user_id: 
            The unique identifier of the user who owns the contact.
        :type user_id: int

        :return: 
            The `Contact` object if found, otherwise `None`.
        :rtype: Contact | None

        :raises SQLAlchemyError:
            If an error occurs while executing the query.

        :example:
            >>> contact = await repository.get_by_id(1, 42)
            >>> if contact:
            ...     print(f"Contact found: {contact.name}")
            ... else:
            ...     print("No contact found.")

        """
        stmt = select(Contact).filter_by(id=id, user_id=user_id)
        contact = await self.session.execute(stmt)
        return contact.scalar_one_or_none()

    async def create(self, contact: Contact) -> Contact:
        """
        Create a new contact and persist it in the database.

        This method adds a new contact to the session, commits the transaction,
        refreshes the instance with the latest database state, and retrieves the 
        newly created contact.

        :param contact: 
            The `Contact` object to be created and stored in the database.
        :type contact: Contact

        :return: 
            The newly created `Contact` object with updated attributes from the database.
        :rtype: Contact

        :raises SQLAlchemyError:
            If an error occurs while committing the transaction.

        :example:
            >>> new_contact = Contact(id=1, user_id=42, name="John Doe", email="john@example.com")
            >>> created_contact = await repository.create(new_contact)
            >>> print(f"Created contact: {created_contact.name}")

        """
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return await self.get_by_id(contact.id, contact.user_id)

    async def update(self, contact: Contact) -> Contact:
        """
        Update an existing contact in the database.

        This method commits changes made to a given `Contact` object,
        refreshes its state to reflect the latest database values, and retrieves 
        the updated contact.

        :param contact: 
            The `Contact` object with modified attributes that need to be updated in the database.
        :type contact: Contact

        :return: 
            The updated `Contact` object with refreshed attributes from the database.
        :rtype: Contact

        :raises SQLAlchemyError:
            If an error occurs while committing the transaction.

        :example:
            >>> contact.name = "Jane Doe"
            >>> updated_contact = await repository.update(contact)
            >>> print(f"Updated contact name: {updated_contact.name}")

        """
        await self.session.commit()
        await self.session.refresh(contact)
        return await self.get_by_id(contact.id, contact.user_id)

    async def remove(self, contact: Contact) -> Contact:
        """
        Delete a contact from the database.

        This method removes the specified `Contact` object from the database,
        commits the transaction, and returns the deleted contact.

        :param contact: 
            The `Contact` object that needs to be deleted.
        :type contact: Contact

        :return: 
            The deleted `Contact` object.
        :rtype: Contact

        :raises SQLAlchemyError:
            If an error occurs while deleting the contact from the database.

        :example:
            >>> contact_to_delete = await repository.get_by_id(1, 42)
            >>> if contact_to_delete:
            ...     deleted_contact = await repository.remove(contact_to_delete)
            ...     print(f"Deleted contact: {deleted_contact.name}")

        """
        await self.session.delete(contact)
        await self.session.commit()
        return contact
