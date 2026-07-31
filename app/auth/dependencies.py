from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repo import AuthRepository
from app.infrastructure.database import Provisioner, get_system_db


async def get_repo_obj(session: AsyncSession = Depends(get_system_db)):
    repo = AuthRepository(session)
    return repo


async def get_provisioner_obj(session: AsyncSession):
    provisioner = Provisioner()
    return provisioner
