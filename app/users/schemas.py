from enum import Enum

from pydantic import BaseModel


class MarketTypeEnum(str, Enum):
    YANDEX = "yandex"


class StoreDataDTO(BaseModel):
    username: str
    market_type: MarketTypeEnum
    api_key: str
    buisness_id: str
