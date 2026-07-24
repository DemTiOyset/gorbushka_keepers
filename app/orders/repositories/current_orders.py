from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.order import Order
from app.infrastructure.models.order_item import OrderItem


class CurrentOrdersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_orders_by_day(self, day: date):
        stmt = select(OrderItem).join(Order).where(func.date(Order.created_at) == day)

        result = await self.session.execute(stmt)
        orders_items = result.scalars().all()

        return orders_items
