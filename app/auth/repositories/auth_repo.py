from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import User


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_username_or_none(self, username: str):
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)

        user_or_none = result.scalar_one_or_none()

        return user_or_none
