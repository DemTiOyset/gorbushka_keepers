from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User


class AuthRepositoryInterface(Protocol):
    async def get_user_by_username_or_none(self, username: str) -> User | None: ...
    async def create_user(self, new_user: dict) -> User: ...
    async def delete_user(self, user: User) -> None: ...
    async def commit(self): ...


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_username_or_none(self, username: str):
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)

        user_or_none = result.scalar_one_or_none()

        return user_or_none

    async def create_user(self, new_user: dict):
        user = User(**new_user)
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete_user(self, user: User) -> None:
        await self.session.delete(user)

    async def commit(self):
        await self.session.commit()
