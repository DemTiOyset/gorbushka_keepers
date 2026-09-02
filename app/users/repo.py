from typing import Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User


class UserRepositoryInfrastructure(Protocol):
    async def get_user_by_business_id_or_none(
        self, business_id: str
    ) -> User | None: ...
    async def get_user_by_campaign_id_or_none(self, campaign_id: int) -> User: ...
    async def create_user_store(
        self, username: str, store_data: dict
    ) -> User | None: ...
    async def commit(self) -> None: ...


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_business_id_or_none(self, business_id: str):
        stmt = select(User).where(User.business_id == business_id)
        result = await self.session.execute(stmt)

        user = result.scalar_one_or_none()

        return user

    async def get_user_by_campaign_id_or_none(self, campaign_id: int) -> User | None:
        stmt = select(User).where(User.campaign_ids.contains([campaign_id]))
        result = await self.session.execute(stmt)

        user = result.scalar_one_or_none()

        return user

    async def create_user_store(self, username: str, store_data: dict):
        stmt = (
            update(User)
            .where(User.username == username)
            .values(**store_data)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        updated_user = result.scalar_one_or_none()
        await self.session.flush()
        return updated_user

    async def commit(self):
        await self.session.commit()
