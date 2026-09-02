"""
Данный модуль - обработка существующих заказов.
"""

from datetime import date

from fastapi import APIRouter, Body, Depends

from app.orders.dependencies import (
    get_market_client_obj,
    get_order_repo_for_user,
    get_tenant_manager,
)
from app.orders.repo import OrdersRepository
from app.orders.schemas import (
    OrderCancelledNotificationSchema,
    OrderCreatedNotificationSchema,
    OrderStatusUpdatedNotificationSchema,
)
from app.orders.services import CurrentOrdersHandler, OrderNotificationHandler
from app.users.dependencies import get_user_repo_obj

router = APIRouter(tags=["orders"])


@router.post("/notification")
async def webhook_listener(
    payload: dict = Body(),
    tenant_manager=Depends(get_tenant_manager),
    user_repo=Depends(get_user_repo_obj),
    market_client=Depends(get_market_client_obj),
):
    notification_type: str | None = payload.get("notificationType")
    handler = OrderNotificationHandler(
        market_client=market_client,
        user_repo=user_repo,
        tenant_manager=tenant_manager,
        order_repo_type=OrdersRepository,  # pyright: ignore[reportArgumentType]
    )
    if notification_type == "ORDER_CREATED":
        order_created_notification = OrderCreatedNotificationSchema.model_validate(
            payload
        )
        result = handler.add_order_created(order_created_notification)

    elif notification_type == "ORDER_STATUS_UPDATED":
        order_updated_notification = (
            OrderStatusUpdatedNotificationSchema.model_validate(payload)
        )
        result = handler.update_order_status(order_updated_notification)

    elif notification_type == "ORDER_CANCELLED":
        cancelled_order_notification = OrderCancelledNotificationSchema.model_validate(
            payload
        )
        result = handler.cancel_order(cancelled_order_notification)


@router.get("/orders")
async def get_orders_by_day(
    day: date,
    repo=Depends(get_order_repo_for_user),
):
    """
    Отображает заказы созданные за указанный день.
    На фронте должна быть возможность выбора даты.
    """
    handler = CurrentOrdersHandler(repo)
    return await handler.handle_get_orders_by_day(day)
