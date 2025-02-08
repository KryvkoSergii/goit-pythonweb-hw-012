from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repository.models import User
from sqlalchemy import select


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user
