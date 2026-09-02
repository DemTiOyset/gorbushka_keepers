from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import TenantSessionManager, get_db
from app.orders.client import MarketClient
from app.orders.repo import OrdersRepository


def get_tenant_manager():
    tenant_manager = TenantSessionManager()

    return tenant_manager


def get_market_client_obj():
    client = MarketClient()

    return client


async def get_order_repo_for_user(
    session: AsyncSession = Depends(get_db),
) -> OrdersRepository:
    return OrdersRepository(session)
