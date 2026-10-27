from typing import Protocol

import httpx

from app.orders.schemas import (
    BusinessOrderSchema,
    GetBusinessOrdersResponseSchema,
    ResponseToMarketSchema,
)


class MarketClientInterface(Protocol):
    async def get_order_data_from_market(
        self, response_data: ResponseToMarketSchema
    ) -> BusinessOrderSchema: ...


class MarketClient:
    async def get_order_data_from_market(
        self,
        response_data: ResponseToMarketSchema,
    ):
        url: str = "https://"
        "api.partner.market.yandex.ru/v1/businesses/"
        f"{response_data.business_id}/orders"
        body = {
            "campaignIds": [response_data.campaign_id],
            "orderIds": [response_data.order_id],
        }

        headers = {
            "Api-Key": response_data.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            payload = resp.json()

        parsed = GetBusinessOrdersResponseSchema.model_validate(payload)

        order_data = parsed.orders[0]

        return order_data
