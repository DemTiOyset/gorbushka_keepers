from fastapi import Depends
from app.infrastructure.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repositories.audit_repo import AuditRepository


async def get_repo_obj(session: AsyncSession = Depends(get_db)):
    repo = AuditRepository(session)

    return repo