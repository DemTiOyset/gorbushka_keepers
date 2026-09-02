from enum import Enum

from pydantic import BaseModel, ConfigDict


class MarketTypeEnum(str, Enum):
    YANDEX = "yandex"


class StoreDataSchema(BaseModel):
    username: str
    market_type: str
    api_key: str
    business_id: str
    campaign_ids: list[int]


class StoreDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    market_type: MarketTypeEnum
    business_id: str
