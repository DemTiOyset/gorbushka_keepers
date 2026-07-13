from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_system_db

from ..repositories.auth_repo import AuthRepository


async def get_repo_obj(session: AsyncSession = Depends(get_system_db)):
    repo = AuthRepository(session)

    return repo
