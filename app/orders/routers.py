"""
Данный модуль - обработка существующих заказов.
"""

from datetime import date

from fastapi import APIRouter, Body, Depends

from app.orders.dependencies import get_repo_obj
from app.orders.schemas import OrderCreatedNotificationDTO
from app.orders.services import CurrentOrdersHandler

router = APIRouter(tags=["orders"])


@router.get("/notification")
async def webhook_listener(payload: dict = Body(), repo=Depends(get_repo_obj)):
    notification_type: str | None = payload.get("notificationType")
    if notification_type == "ORDER_CREATED":
        order_created_notification = OrderCreatedNotificationDTO.model_validate(payload)
        ...


@router.get("/")
async def get_orders_by_day(day: date, repo=Depends(get_repo_obj)):
    """
    Этот роут отображает заказы созданные за указанный день, на страничке должна быть возможность выбора даты.
    """
    handler = CurrentOrdersHandler(repo)
    return await handler.handle_get_orders_by_day(day)
