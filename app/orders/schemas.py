from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class OrderStatusType(str, Enum):
    PLACING = "PLACING"
    RESERVED = "RESERVED"
    UNPAID = "UNPAID"
    PROCESSING = "PROCESSING"
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"
    PARTIALLY_RETURNED = "PARTIALLY_RETURNED"
    RETURNED = "RETURNED"
    UNKNOWN = "UNKNOWN"

    @property
    def label(self) -> str:
        return {
            self.PLACING: "Оформляется",
            self.RESERVED: "Зарезервирован",
            self.UNPAID: "Не оплачен",
            self.PROCESSING: "В обработке",
            self.DELIVERY: "Передан в доставку",
            self.PICKUP: "Ожидает получения",
            self.DELIVERED: "Получен покупателем",
            self.CANCELLED: "Отменён",
            self.PENDING: "Ожидает обработки",
            self.PARTIALLY_RETURNED: "Частично возвращён",
            self.RETURNED: "Полностью возвращён",
            self.UNKNOWN: "Неизвестный статус",
        }[self]


class ReturnType(str, Enum):
    UNREDEEMED = "UNREDEEMED"
    RETURN = "RETURN"


class OrderUpdateType(str, Enum):
    SHIPMENT_DATE_UPDATED = "SHIPMENT_DATE_UPDATED"
    DELIVERY_DATE_UPDATED = "DELIVERY_DATE_UPDATED"
    UNKNOWN = "UNKNOWN"


# ============================================================
# Common DTO
# ============================================================


class NotificationOrderItemDTO(BaseSchema):
    offer_id: str = Field(alias="offerId")
    count: int


class NotificationReturnItemDTO(BaseSchema):
    offer_id: str = Field(alias="offerId")
    count: int


# ============================================================
# Base notification
# ============================================================


class BaseOrderNotificationDTO(BaseSchema):
    order_id: int = Field(alias="orderId")
    campaign_id: int = Field(alias="campaignId")


# ============================================================
# Notifications
# ============================================================


class OrderCreatedNotificationDTO(BaseOrderNotificationDTO):
    notification_type: Literal[NotificationType.ORDER_CREATED] = Field(
        alias="notificationType"
    )

    items: list[NotificationOrderItemDTO]

    created_at: datetime = Field(alias="createdAt")


class OrderCancelledNotificationDTO(BaseOrderNotificationDTO):
    notification_type: Literal[NotificationType.ORDER_CANCELLED] = Field(
        alias="notificationType"
    )

    items: list[NotificationOrderItemDTO]

    cancelled_at: datetime = Field(alias="cancelledAt")


class OrderStatusUpdatedNotificationDTO(BaseOrderNotificationDTO):
    notification_type: Literal[NotificationType.ORDER_STATUS_UPDATED] = Field(
        alias="notificationType"
    )

    #
    # Документация допускает неизвестные значения,
    # поэтому оставляем str.
    #
    status: str

    #
    # Полный перечень substatus очень большой.
    #
    substatus: str

    updated_at: datetime = Field(alias="updatedAt")


class OrderReturnCreatedNotificationDTO(BaseOrderNotificationDTO):
    notification_type: Literal[NotificationType.ORDER_RETURN_CREATED] = Field(
        alias="notificationType"
    )

    return_id: int = Field(alias="returnId")

    return_type: ReturnType = Field(alias="returnType")

    items: list[NotificationReturnItemDTO]

    created_at: datetime = Field(alias="createdAt")


class OrderUpdatedNotificationDTO(BaseOrderNotificationDTO):
    notification_type: Literal[NotificationType.ORDER_UPDATED] = Field(
        alias="notificationType"
    )

    update_type: OrderUpdateType = Field(alias="updateType")

    updated_at: datetime = Field(alias="updatedAt")


class MoneyDTO(BaseModel):
    value: float
    currencyId: str


class DeliveryPricesDTO(BaseModel):
    payment: MoneyDTO | None = None
    subsidy: MoneyDTO | None = None
    vat: str | None = None


class OrderPricesDTO(BaseModel):
    payment: MoneyDTO | None = None
    subsidy: MoneyDTO | None = None
    cashback: MoneyDTO | None = None
    delivery: DeliveryPricesDTO | None = None


class ItemPricesDTO(BaseModel):
    payment: MoneyDTO | None = None
    subsidy: MoneyDTO | None = None
    cashback: MoneyDTO | None = None
    vat: str | None = None


class BusinessOrderItemDTO(BaseModel):
    id: int
    offerId: str
    offerName: str
    count: int
    prices: ItemPricesDTO | None = None


class BusinessOrderShipmentDTO(BaseModel):
    id: int
    shipmentDate: datetime
    shipmentTime: str | None = None


class DeliveryOrderDatesDTO(BaseModel):
    shipment: BusinessOrderShipmentDTO | None = None


class BusinessOrderDTO(BaseModel):
    orderId: int
    campaignId: int
    status: str
    substatus: str | None = None
    items: list[BusinessOrderItemDTO]
    prices: OrderPricesDTO | None = None
    delivery: DeliveryOrderDatesDTO | None = None


class GetBusinessOrdersResponseDTO(BaseModel):
    orders: list[BusinessOrderDTO]
    paging: dict = {}
