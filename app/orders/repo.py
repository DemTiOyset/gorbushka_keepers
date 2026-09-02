from datetime import date
from typing import Protocol, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.order import Order
from app.infrastructure.models.order_item import OrderItem
from app.orders.schemas import CreateOrderItemSchema, CreateOrderSchema


class OrdersRepositoryInterface(Protocol):
    async def get_orders_by_day(self, day: date) -> Sequence[OrderItem]: ...
    async def get_orders_with_items_by_day(self, day: date) -> Sequence[Order]: ...
    async def get_order_by_posting_number_or_none(self, order_id: int) -> Order: ...
    async def commit(self) -> None: ...
    async def create_order_with_items(
        self, order: CreateOrderSchema, order_items: list[CreateOrderItemSchema]
    ) -> Order: ...
    async def update_order_status(self, order: Order, new_status: str): ...
    async def cancel_order(self, order: Order): ...
    async def reduce_order_item_count(self, order_item: OrderItem, count: int): ...
    async def get_order_item_by_offer_id_order_id(
        self, order_id: int, offer_id: str
    ) -> OrderItem | None: ...


class OrdersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_orders_by_day(self, day: date):
        stmt = select(OrderItem).join(Order).where(func.date(Order.created_at) == day)

        result = await self.session.execute(stmt)
        orders_items = result.scalars().all()

        return orders_items

    async def get_orders_with_items_by_day(self, day: date):
        stmt = (
            select(Order)
            .where(func.date(Order.created_at) == day)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )

        result = await self.session.execute(stmt)
        orders = result.scalars().all()

        return orders

    async def get_order_by_posting_number_or_none(self, order_id: int):
        stmt = select(Order).where(Order.order_id == order_id)

        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()

        return order

    async def create_order_with_items(
        self,
        order_data: CreateOrderSchema,
        order_items_data: list[CreateOrderItemSchema],
    ) -> Order:
        order_items_model = [
            OrderItem(**item.model_dump()) for item in order_items_data
        ]
        order_model: Order = Order(**order_data.model_dump(), items=order_items_model)
        self.session.add(order_model)

        await self.session.flush()

        return order_model

    async def update_order_status(self, order: Order, new_status: str):
        order.status = new_status

    async def cancel_order(self, order: Order):
        order.is_cancelled = True

    async def reduce_order_item_count(self, order_item: OrderItem, count: int):
        order_item.count -= count

    async def get_order_item_by_offer_id_order_id(
        self, order_id: int, offer_id: str
    ) -> OrderItem | None:
        stmt = select(OrderItem).where(
            OrderItem.order_id == order_id, OrderItem.offer_id == offer_id
        )
        result = await self.session.execute(stmt)
        order_item = result.scalar_one_or_none()

        return order_item

    async def commit(self) -> None:
        await self.session.commit()
