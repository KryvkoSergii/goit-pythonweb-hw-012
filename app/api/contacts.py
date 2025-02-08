from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import ContractModel, ContactsQuery, ContactBase
from database.db import get_db
from services.contacts import ContactService
from logger.logger import build_logger
from fastapi import Path, Query
from schemas import ErrorsContent, UserModel
import datetime
from services.auth import get_current_user

logger = build_logger("contacts_app", "DEBUG")
router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=List[ContractModel],
    responses={422: {"model": ErrorsContent}, 500: {"model": ErrorsContent}},
)
async def read_contacts(
    skip: int = Query(
        default=0,
        description="The number of records to skip before starting to return results",
    ),
    limit: int = Query(
        default=10, le=100, ge=10, description="Number of records per response"
    ),
    first_name: str | None = Query(default=None, description="Contact first name"),
    last_name: str | None = Query(default=None, description="Contact last name"),
    email: str | None = Query(default=None, description="Contact email"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    query = ContactsQuery(
        skip=skip,
        limit=limit,
        first_name=first_name,
        last_name=last_name,
        email=email,
        user_id=current_user.id,
    )
    service = ContactService(logger=logger, db=db)
    contacts = await service.get_by_query(query)
    return contacts


@router.post(
    "/",
    response_model=ContractModel,
    responses={422: {"model": ErrorsContent}, 500: {"model": ErrorsContent}},
    status_code=status.HTTP_201_CREATED,
)
async def create_contacts(
    request: ContactBase,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(logger=logger, db=db)
    contact = await service.create(request, current_user)
    return contact


@router.put(
    "/{contact_id}",
    response_model=ContractModel,
    responses={
        400: {"model": ErrorsContent},
        404: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def update_contacts(
    request: ContractModel,
    contact_id: int = Path(description="Contact id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(logger=logger, db=db)
    contact = await service.update(contact_id, request, current_user)
    return contact


@router.delete(
    "/{contact_id}",
    response_model=ContractModel,
    responses={
        404: {"model": ErrorsContent},
        422: {"model": ErrorsContent},
        500: {"model": ErrorsContent},
    },
)
async def delete_contacts(
    contact_id: int = Path(description="Contact id"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    service = ContactService(logger=logger, db=db)
    contact = await service.remove(contact_id, current_user)
    return contact


@router.get(
    "/birthdays",
    response_model=List[ContractModel],
    responses={422: {"model": ErrorsContent}, 500: {"model": ErrorsContent}},
)
async def read_contacts_with_birthdays_in_7_days(
    skip: int = Query(
        default=0,
        description="The number of records to skip before starting to return results",
    ),
    limit: int = Query(
        default=10, le=100, ge=10, description="Number of records per response"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    query = ContactsQuery(
        skip=skip,
        limit=limit,
        date_from=datetime.date.today(),
        date_to=datetime.date.today() + datetime.timedelta(days=7),
        user_id=current_user.id,
    )
    service = ContactService(logger=logger, db=db)
    contacts = await service.get_by_query(query)
    return contacts
