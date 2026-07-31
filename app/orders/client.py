async def get_order(
    campaign_id: int,
    order_id: int,
    url: str = f"https://"
    f"api.partner.market.yandex.ru/v1/businesses/"
    f"{settings.business_id}/orders",
):
    body = {"campaignIds": [campaign_id], "orderIds": [order_id]}

    headers = {
        "Api-Key": settings.api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        payload = resp.json()

    parsed = GetBusinessOrdersResponseDTO.model_validate(payload)

    order_data = parsed.orders[0]

    return order_data
