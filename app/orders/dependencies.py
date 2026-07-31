from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.orders.repo import OrdersRepository


async def get_repo_obj(session: AsyncSession = Depends(get_db)):
    repo = OrdersRepository(session)

    return repo
