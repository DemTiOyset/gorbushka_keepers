from datetime import date
from decimal import Decimal
import logging
from typing import Any

logger = logging.getLogger(__name__)

from app.infrastructure.database import TenantSessionManagerInterface
from app.orders.client import MarketClientInterface
from app.orders.repo import OrdersRepositoryInterface
from app.orders.schemas import (
    BusinessOrderSchema,
    CancellationsAndReturnsSchema,
    CreateOrderItemSchema,
    CreateOrderSchema,
    OrderCancelledNotificationSchema,
    OrderCreatedNotificationSchema,
    OrderItemResponseSchema,
    OrderResponseSchema,
    OrderReturnCreatedNotificationSchema,
    OrdersDayResponseSchema,
    OrderStatusUpdatedNotificationSchema,
    ResponseToMarketSchema,
)
from app.users.repo import UserRepositoryInfrastructure


class OrderNotificationHandler:
    def __init__(
        self,
        tenant_manager: TenantSessionManagerInterface,
        user_repo: UserRepositoryInfrastructure,
        market_client: MarketClientInterface,
        order_repo_type: OrdersRepositoryInterface,
    ):
        self.tenant_manager = tenant_manager
        self.user_repo = user_repo
        self.market_client = market_client
        self.order_repo_type = order_repo_type

    async def add_order_created(
        self, notification: OrderCreatedNotificationSchema | Any
    ):
        user_from_db = await self.user_repo.get_user_by_campaign_id_or_none(
            notification.campaign_id
        )

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.order_repo_type,  # pyright: ignore[reportArgumentType]
        ) as order_repo:
            existing_order = await order_repo.get_order_by_posting_number_or_none(
                notification.order_id
            )

            if existing_order:
                return

            response_to_market_data = ResponseToMarketSchema(
                campaign_id=notification.campaign_id,
                order_id=notification.order_id,
                business_id=user_from_db.business_id,
                api_key=user_from_db.api_key,
            )

            order_data: BusinessOrderSchema = (
                await self.market_client.get_order_data_from_market(
                    response_data=response_to_market_data
                )
            )

            if order_data is not None:
                order_expected_payout = float(0)
                if order_data.prices:
                    order_expected_payout = (
                        order_data.prices.cashback.value
                        + order_data.prices.payment.value
                        + order_data.prices.subsidy.value
                    )

                order_items: list[CreateOrderItemSchema] = []

                for item in order_data.items:
                    item_prices = item.prices
                    order_item_schema = CreateOrderItemSchema(
                        offer_id=item.offer_id,
                        offer_name=item.offer_name,
                        count=item.count,
                        payment=Decimal(str(item_prices.payment.value)),
                        subsidy=Decimal(str(item_prices.subsidy.value)),
                        cashback=Decimal(str(item_prices.cashback.value)),
                        vat=Decimal(str(item_prices.vat)),
                    )
                    order_items.append(order_item_schema)

                order = CreateOrderSchema(
                    order_id=order_data.order_id,
                    expected_payout=order_expected_payout,
                    status=order_data.status,
                    campaign_id=order_data.campaign_id,
                )

                await order_repo.create_order_with_items(order, order_items)

                await order_repo.commit()

        return "ok"

    async def update_order_status(
        self, notification: OrderStatusUpdatedNotificationSchema
    ):
        user_from_db = await self.user_repo.get_user_by_campaign_id_or_none(
            notification.campaign_id
        )

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.order_repo_type,  # pyright: ignore[reportArgumentType]
        ) as order_repo:
            existing_order = await order_repo.get_order_by_posting_number_or_none(
                notification.order_id
            )

            if existing_order is None:
                await self.add_order_created(notification=notification)

            if (
                existing_order.last_update_time is not None  # pyright: ignore[reportOptionalMemberAccess]
                and existing_order.last_update_time > notification.updated_at  # pyright: ignore[reportOptionalMemberAccess]
            ):
                return

            await order_repo.update_order_status(
                order=existing_order, new_status=notification.status
            )

            await order_repo.commit()

        return "ok"

    async def cancel_order(self, notification: OrderCancelledNotificationSchema):
        user_from_db = await self.user_repo.get_user_by_campaign_id_or_none(
            notification.campaign_id
        )

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.order_repo_type,  # pyright: ignore[reportArgumentType]
        ) as order_repo:
            existing_order = await order_repo.get_order_by_posting_number_or_none(
                notification.order_id
            )

            if existing_order is None:
                await self.add_order_created(notification=notification)

            if (
                existing_order.last_cancel_time is not None  # pyright: ignore[reportOptionalMemberAccess]
                and existing_order.last_cancel_time > notification.cancelled_at  # pyright: ignore[reportOptionalMemberAccess]
            ):
                return

            await order_repo.cancel_order(order=existing_order)

            await order_repo.commit()

        return "ok"

    async def create_return_order(
        self, notification: OrderReturnCreatedNotificationSchema
    ):
        user_from_db = await self.user_repo.get_user_by_campaign_id_or_none(
            notification.campaign_id
        )

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.order_repo_type,  # pyright: ignore[reportArgumentType]
        ) as order_repo:
            existing_order = await order_repo.get_order_by_posting_number_or_none(
                notification.order_id
            )

            if existing_order is None:
                return await self.add_order_created(notification=notification)

            if (
                existing_order.last_return_time is not None
                and existing_order.last_return_time > notification.created_at
            ):
                return

            for item in notification.items:
                existing_item = await order_repo.get_order_item_by_offer_id_order_id(
                    order_id=existing_order.order_id, offer_id=item.offer_id
                )
                if existing_item is None:
                    return

                if existing_item.count < item.count:
                    return

                await order_repo.reduce_order_item_count(
                    order_item=existing_item, count=item.count
                )

                await order_repo.add_order_item_returned_count(
                    order_item=existing_item, count=item.count
                )
                await order_repo.mark_return_type_order_item(
                    order_item=existing_item, return_type=notification.return_type.value
                )

                try:
                    from app.tg_bot.notifier import send_return_notification

                    await send_return_notification(
                        order_id=existing_order.order_id,
                        item_id=existing_item.id,
                        offer_name=existing_item.offer_name,
                        offer_id=existing_item.offer_id,
                        count=item.count,
                        return_type=notification.return_type.value,
                        campaign_id=notification.campaign_id,
                    )
                except Exception as exc:
                    logger.warning(
                        f"Не удалось отправить Telegram-уведомление о возврате: {exc}"
                    )

            await order_repo.mark_has_returned_order(existing_order)

            await order_repo.commit()

        return "ok"


class CurrentOrdersHandler:
    def __init__(self, repo: OrdersRepositoryInterface):
        self.repo = repo

    async def handle_get_orders_by_day(
        self,
        day: date,
        earlier: bool = True,
    ):
        orders_from_db = await self.repo.get_orders_with_items_by_day(day)
        if not orders_from_db:
            return OrdersDayResponseSchema(orders=[])

        response_orders = [
            OrderResponseSchema.model_validate(order) for order in orders_from_db
        ]

        return OrdersDayResponseSchema(orders=response_orders)


class ReturnsHandler:
    def __init__(self, repo: OrdersRepositoryInterface):
        self.repo = repo

    async def handle_get_returns_and_cancellations(self):
        cancellations = await self.repo.get_cancellations()
        returns = await self.repo.get_returns()

        response_cancellations = [
            OrderResponseSchema.model_validate(order) for order in cancellations
        ]

        response_returns = [
            OrderItemResponseSchema.model_validate(order_item) for order_item in returns
        ]
        response_schema = CancellationsAndReturnsSchema(
            cancellations=response_cancellations, returns=response_returns
        )

        return response_schema
