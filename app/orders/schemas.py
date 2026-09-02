from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


# ============================================================
# Enums
# ============================================================


class NotificationType(str, Enum):
    PING = "PING"

    ORDER_CREATED = "ORDER_CREATED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_STATUS_UPDATED = "ORDER_STATUS_UPDATED"
    ORDER_RETURN_CREATED = "ORDER_RETURN_CREATED"
    ORDER_CANCELLATION_REQUEST = "ORDER_CANCELLATION_REQUEST"
    ORDER_RETURN_STATUS_UPDATED = "ORDER_RETURN_STATUS_UPDATED"
    ORDER_UPDATED = "ORDER_UPDATED"


STATUS = {
    "PLACING": "Оформляется",
    "RESERVED": "Зарезервирован",
    "UNPAID": "Не оплачен",
    "PROCESSING": "В обработке",
    "DELIVERY": "Передан в доставку",
    "PICKUP": "Ожидает получения",
    "DELIVERED": "Получен покупателем",
    "CANCELLED": "Отменён",
    "PENDING": "Ожидает обработки",
    "PARTIALLY_RETURNED": "Частично возвращён",
    "RETURNED": "Полностью возвращён",
    "UNKNOWN": "Неизвестный статус",
}


class ReturnType(str, Enum):
    UNREDEEMED = "UNREDEEMED"
    RETURN = "RETURN"


class OrderUpdateType(str, Enum):
    SHIPMENT_DATE_UPDATED = "SHIPMENT_DATE_UPDATED"
    DELIVERY_DATE_UPDATED = "DELIVERY_DATE_UPDATED"
    UNKNOWN = "UNKNOWN"


# ============================================================
# Common Schema
# ============================================================


class NotificationOrderItemSchema(BaseSchema):
    offer_id: str = Field(alias="offerId")
    count: int


class NotificationReturnItemSchema(BaseSchema):
    offer_id: str = Field(alias="offerId")
    count: int


# ============================================================
# Base notification
# ============================================================


class BaseOrderNotificationSchema(BaseSchema):
    order_id: int = Field(alias="orderId")
    campaign_id: int = Field(alias="campaignId")


# ============================================================
# Notifications
# ============================================================


class OrderCreatedNotificationSchema(BaseOrderNotificationSchema):
    notification_type: Literal[NotificationType.ORDER_CREATED] = Field(
        alias="notificationType"
    )

    items: list[NotificationOrderItemSchema]

    created_at: datetime = Field(alias="createdAt")


class OrderCancelledNotificationSchema(BaseOrderNotificationSchema):
    notification_type: Literal[NotificationType.ORDER_CANCELLED] = Field(
        alias="notificationType"
    )

    items: list[NotificationOrderItemSchema]

    cancelled_at: datetime = Field(alias="cancelledAt")


class OrderStatusUpdatedNotificationSchema(BaseOrderNotificationSchema):
    notification_type: Literal[NotificationType.ORDER_STATUS_UPDATED] = Field(
        alias="notificationType"
    )

    #
    # Документация допускает неизвестные значения,
    # поэтому оставляем str.
    #
    status: str

    updated_at: datetime = Field(alias="updatedAt")


class OrderReturnCreatedNotificationSchema(BaseOrderNotificationSchema):
    notification_type: Literal[NotificationType.ORDER_RETURN_CREATED] = Field(
        alias="notificationType"
    )

    return_id: int = Field(alias="returnId")

    return_type: ReturnType = Field(alias="returnType")

    items: list[NotificationReturnItemSchema]

    created_at: datetime = Field(alias="createdAt")


class OrderUpdatedNotificationSchema(BaseOrderNotificationSchema):
    notification_type: Literal[NotificationType.ORDER_UPDATED] = Field(
        alias="notificationType"
    )

    update_type: OrderUpdateType = Field(alias="updateType")

    updated_at: datetime = Field(alias="updatedAt")


class MoneySchema(BaseModel):
    value: float
    currency_id: str = Field(alias="currencyId")


class DeliveryPricesSchema(BaseModel):
    payment: MoneySchema | None = None
    subsidy: MoneySchema | None = None
    vat: str | None = None


class OrderPricesSchema(BaseModel):
    payment: MoneySchema
    subsidy: MoneySchema
    cashback: MoneySchema
    delivery: DeliveryPricesSchema | None = None


class ItemPricesSchema(BaseModel):
    payment: MoneySchema
    subsidy: MoneySchema
    cashback: MoneySchema
    vat: str


class BusinessOrderItemSchema(BaseModel):
    offer_id: str = Field(alias="offerId")
    offer_name: str = Field(alias="offerName")
    count: int
    prices: ItemPricesSchema


class BusinessOrderShipmentSchema(BaseModel):
    shipment_date: datetime = Field(alias="shipmentDate")
    shipment_time: str | None = Field(default=None, alias="shipmentTime")


class DeliveryOrderDatesSchema(BaseModel):
    shipment: BusinessOrderShipmentSchema | None = None


class BusinessOrderSchema(BaseModel):
    order_id: int = Field(alias="orderId")
    campaign_id: int = Field(alias="campaignId")
    status: str
    substatus: str | None = None
    items: list[BusinessOrderItemSchema]
    prices: OrderPricesSchema | None = None
    delivery: DeliveryOrderDatesSchema | None = None


class GetBusinessOrdersResponseSchema(BaseModel):
    orders: list[BusinessOrderSchema]
    paging: dict = {}


class ResponseToMarketSchema(BaseModel):
    campaign_id: int
    order_id: int
    business_id: str
    api_key: str


class CreateOrderItemSchema(BaseModel):
    offer_id: str
    offer_name: str
    count: int
    payment: Decimal
    subsidy: Decimal
    cashback: Decimal
    vat: Decimal  # процент НДС (напр. 0.00 или 0.20), приводится к Decimal


class CreateOrderSchema(BaseModel):
    order_id: int
    campaign_id: int
    status: str
    expected_payout: float


# ============================================================
# Response schemas — для GET /orders?day=...
# ============================================================


class OrderItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: str
    offer_name: str
    count: int
    payment: Decimal
    subsidy: Decimal
    cashback: Decimal
    vat: Decimal


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    campaign_id: int
    created_at: datetime
    status: str
    expected_payout: Decimal
    payout: Decimal | None = None
    items: list[OrderItemResponseSchema]

    @field_validator("status", mode="after")
    @classmethod
    def translate_status(cls, value: str) -> str:
        translated_status = STATUS.get(value, STATUS["UNKNOWN"])
        return translated_status


class OrdersDayResponseSchema(BaseModel):
    orders: list[OrderResponseSchema]
