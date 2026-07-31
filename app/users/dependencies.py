from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.users.repo import UserRepository


async def get_repo_obj(session: AsyncSession = Depends(get_db)):
    repo = UserRepository(session)

    return repo
