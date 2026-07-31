from datetime import date

from app.orders.repo import OrdersRepositoryInterface
from app.orders.schemas import OrderCreatedNotificationDTO


class CurrentOrdersHandler:
    def __init__(self, repo: OrdersRepositoryInterface):
        self.repo = repo

    async def handle_order_created(self, notification: OrderCreatedNotificationDTO):
        existing_order = await self.repo.get_order_by_posting_number_or_none(
            notification.posting_number
        )

        if existing_order:
            return

        order_data: ReceivedOrderDTO = await self._get_parsed_order_from_market(
            notification.posting_number
        )

        if order_data is not None:
            order_expected_payout = Decimal(0)
            order_item_models: list[OrderItem] = []

            for item, item_financial_data in zip(
                order_data.products, order_data.financial_data.products
            ):
                order_item_model = await OrderValidation.convert_item_to_model(
                    item, item_financial_data
                )
                order_item_models.append(order_item_model)
                order_expected_payout += item_financial_data.payout

            order_model = OrderValidation.convert_order_to_model(
                order_data, order_expected_payout
            )

            await self.repo.create_order_with_items(order_model, order_item_models)

            await self.repo.session.commit()

        return HandlerResponse.OK

    # async def handle_get_orders_by_day(self, day: date):
    #     orders_from_db = await self.repo.get_orders_by_day(day)
    #     if not orders_from_db:
    #         return OrdersDayResponseSchema.model_validate({"items": []})
    #     orders = OrdersDayResponseSchema.model_validate({"items": orders_from_db})
    #     return orders
