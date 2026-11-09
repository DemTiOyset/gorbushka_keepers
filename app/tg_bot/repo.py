from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.order_item import OrderItem


class TelegramBotRepositoryInterface(Protocol):
    async def get_user(self, telegram_id: int) -> list[OrderItem]: ...
    async def get_order_item(self, item_id) -> OrderItem | None: ...
    async def commit(self): ...


class TelegramBotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_returned_orders(self):
        stmt = select(OrderItem).where(
            OrderItem.returned_count > 0,
            OrderItem.is_returned_finished.is_(False),
        )
        res = await self.session.execute(stmt)
        items = res.scalars().all()

        return items

    async def get_order_item(self, item_id):
        stmt = select(OrderItem).where(OrderItem.id == item_id)
        res = await self.session.execute(stmt)
        order_item = res.scalar_one_or_none()

        return order_item

    async def commit(self):
        await self.session.commit()
