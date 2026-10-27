from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repo import AuditRepository
from app.infrastructure.database import get_db


async def get_repo_obj(session: AsyncSession = Depends(get_db)):
    repo = AuditRepository(session)

    return repo
