from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UserRepositoryInfrastructure(Protocol): ...


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
