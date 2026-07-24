from datetime import date

from app.orders.repositories.current_orders import CurrentOrdersRepository
from app.orders.schemas.current_orders import OrdersDayResponseSchema


class CurrentOrdersHandler:
    def __init__(self, repo):
        self.repo = repo

    async def handle_get_orders_by_day(self, day: date):
        orders_from_db = await self.repo.get_orders_by_day(day)
        if not orders_from_db:
            return OrdersDayResponseSchema.model_validate({"items": []})
        orders = OrdersDayResponseSchema.model_validate({"items": orders_from_db})
        return orders
