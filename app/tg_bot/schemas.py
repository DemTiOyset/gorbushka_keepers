from pydantic import BaseModel


class BaseRequest(BaseModel):
    telegram_id: int


class SetStatusRequest(BaseRequest):
    item_id: int
    is_finished: bool


class GetOrderRequest(BaseRequest):
    item_id: int


class OrderItemResponse(BaseModel):
    username: str
    item_id: int
    order_id: int
    offer_id: str
    offer_name: str
    returned_count: int
    return_type: str
    is_returned_finished: bool
