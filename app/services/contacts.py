from sqlalchemy.ext.asyncio import AsyncSession
from repository.contacts import ContactRepository
from schemas import ContactsQuery, ContractModel, ContactBase, UserModel
from repository.models import Contact
from logging import Logger
from typing import List
from errors import ContactNotFoundError
from datetime import datetime


class ContactService:
    """
    Service layer for managing contact-related operations.

    This class provides methods for searching, creating, updating, 
    and removing contacts while interacting with the `ContactRepository`.
    """

    def __init__(self, logger: Logger, db: AsyncSession):
        """
        Initialize a `ContactService` instance.

        :param logger: Logger instance for logging contact-related events.
        :type logger: Logger

        :param db: AsyncSession for database operations.
        :type db: AsyncSession
        """
        self.__contact_repository: ContactRepository = ContactRepository(db)
        self.__logger: Logger = logger

    async def get_by_query(self, query: ContactsQuery) -> List[ContractModel]:
        """
        Retrieve a list of contacts based on query parameters.

        :param query: Query parameters for filtering contacts.
        :type query: ContactsQuery

        :return: A list of matching contacts as `ContractModel` objects.
        :rtype: List[ContractModel]

        :raises SQLAlchemyError:
            If an error occurs during the query execution.

        :example:
            >>> contacts = await contact_service.get_by_query(query)
            >>> for contact in contacts:
            ...     print(contact.first_name)
        """
        self.__logger.debug(f"Searching for contacts by '{query}'")
        entities = await self.__contact_repository.get_list_by_query(query)
        return list(map(lambda c: self.__transform_contact_to_contract_model(c), entities))

    async def create(self, contact: ContactBase, current_user: UserModel) -> ContractModel:
        """
        Create a new contact.

        :param contact: The contact details to be created.
        :type contact: ContactBase

        :param current_user: The user who owns the contact.
        :type current_user: UserModel

        :return: The created contact as a `ContractModel`.
        :rtype: ContractModel

        :raises SQLAlchemyError:
            If an error occurs during the database operation.

        :example:
            >>> new_contact = ContactBase(first_name="John", last_name="Doe", email="john@example.com")
            >>> created_contact = await contact_service.create(new_contact, current_user)
            >>> print(f"Created contact: {created_contact.first_name}")
        """
        self.__logger.info(
            f"Creating contact: '{contact}' by: '{current_user.username}'")
        date = None
        if contact.date:
            date = datetime.strptime(contact.date, "%Y-%m-%d").date()

        entity = Contact(
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            date=date,
            notes=contact.notes,
            user_id=current_user.id,
        )

        contact = await self.__contact_repository.create(entity)
        return self.__transform_contact_to_contract_model(contact)

    async def update(self, id: int, contact: ContractModel, current_user: UserModel) -> ContractModel:
        """
        Update an existing contact.

        :param id: The ID of the contact to be updated.
        :type id: int

        :param contact: The updated contact details.
        :type contact: ContractModel

        :param current_user: The user who owns the contact.
        :type current_user: UserModel

        :return: The updated contact as a `ContractModel`.
        :rtype: ContractModel

        :raises ValueError:
            If the provided ID does not match the contact ID.

        :raises ContactNotFoundError:
            If the contact with the specified ID does not exist.

        :example:
            >>> updated_contact = await contact_service.update(1, updated_contact_data, current_user)
            >>> print(f"Updated contact name: {updated_contact.first_name}")
        """
        self.__logger.info(
            f"Updating contact by id: '{id}' content: '{contact}' by: '{current_user.username}'")
        if id != contact.id:
            raise ValueError(
                f"Id in request mismatch. Request: '{id}', body: '{contact.id}'")

        persisted = await self.__contact_repository.get_by_id(id, current_user.id)
        if not persisted:
            raise ContactNotFoundError(id)

        for key, value in contact.__dict__.items():
            if key == "date":
                value = datetime.strptime(
                    contact.date, "%Y-%m-%d").date() if contact.date else None
            setattr(persisted, key, value)

        contact = await self.__contact_repository.update(persisted)
        return self.__transform_contact_to_contract_model(contact)

    async def remove(self, id: int, current_user: UserModel) -> ContractModel:
        """
        Remove a contact by ID.

        :param id: The ID of the contact to be removed.
        :type id: int

        :param current_user: The user who owns the contact.
        :type current_user: UserModel

        :return: The removed contact as a `ContractModel`.
        :rtype: ContractModel

        :raises ContactNotFoundError:
            If the contact with the specified ID does not exist.

        :example:
            >>> removed_contact = await contact_service.remove(1, current_user)
            >>> print(f"Removed contact: {removed_contact.first_name}")
        """
        self.__logger.info(
            f"Removing contact by id: '{id}' by: '{current_user.username}'")
        persisted = await self.__contact_repository.get_by_id(id, current_user.id)
        if not persisted:
            raise ContactNotFoundError(id)
        await self.__contact_repository.remove(persisted)
        return self.__transform_contact_to_contract_model(persisted)

    def __transform_contact_to_contract_model(self, contact: Contact) -> ContractModel:
        """
        Transform a `Contact` entity into a `ContractModel`.

        :param contact: The `Contact` object to be transformed.
        :type contact: Contact

        :return: The transformed `ContractModel` object.
        :rtype: ContractModel

        :example:
            >>> contact_entity = Contact(first_name="John", last_name="Doe", email="john@example.com")
            >>> contact_model = contact_service._ContactService__transform_contact_to_contract_model(contact_entity)
            >>> print(contact_model.first_name)  # Output: John
        """
        return ContractModel(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            date=contact.date.isoformat(),
            notes=contact.notes,
        )
