"""
Интеграционные тесты роутеров.

Проверяют HTTP-слой:
  - POST /notification (ORDER_CREATED, ORDER_STATUS_UPDATED, ORDER_CANCELLED,
                        ORDER_RETURN_CREATED с returnType=RETURN и UNREDEEMED)
  - GET /orders?day=...
  - GET /returns

Требования к окружению (те же, что и у test_add_order_created.py):
  - запущен стек (make up / make prod)
  - создан пользователь test_user (make create-user) и привязан магазин (make bind-store):
      Business ID: 123456, API key: test-api-key, Campaign ids: 100500 100501

Запуск:

    docker compose exec backend uv run pytest tests/test_routers.py -v -s
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database import (
    Base,
    Provisioner,
    async_session_maker,
    get_db,
    get_sessionmaker,
)
from app.infrastructure.models.user import User
from app.main import app
from app.orders.dependencies import get_market_client_obj
from app.orders.schemas import (
    BusinessOrderItemSchema,
    BusinessOrderSchema,
    DeliveryOrderDatesSchema,
    ItemPricesSchema,
    MoneySchema,
    OrderPricesSchema,
    ResponseToMarketSchema,
)

TEST_USERNAME = "test_user"

# Уникальные ID заказов, чтобы не конфликтовать с seed-данными (777001–777005).
ORDER_IDS = [999001, 999002, 999003, 999004]


class FakeMarketClient:
    """Возвращает тестовые данные вместо обращения к API Яндекс Маркета."""

    async def get_order_data_from_market(
        self, response_data: ResponseToMarketSchema
    ) -> BusinessOrderSchema:
        oid = response_data.order_id
        cid = response_data.campaign_id
        return BusinessOrderSchema(
            orderId=oid,
            campaignId=cid,
            status="PROCESSING",
            substatus="STARTED",
            items=[
                BusinessOrderItemSchema(
                    offerId=f"SKU-{oid}-A",
                    offerName=f"Товар A (заказ #{oid})",
                    count=2,
                    prices=ItemPricesSchema(
                        payment=MoneySchema(value=2000.0, currencyId="RUR"),
                        subsidy=MoneySchema(value=100.0, currencyId="RUR"),
                        cashback=MoneySchema(value=50.0, currencyId="RUR"),
                        vat="0.20",
                    ),
                ),
                BusinessOrderItemSchema(
                    offerId=f"SKU-{oid}-B",
                    offerName=f"Товар B (заказ #{oid})",
                    count=1,
                    prices=ItemPricesSchema(
                        payment=MoneySchema(value=1500.0, currencyId="RUR"),
                        subsidy=MoneySchema(value=0.0, currencyId="RUR"),
                        cashback=MoneySchema(value=0.0, currencyId="RUR"),
                        vat="0.20",
                    ),
                ),
            ],
            prices=OrderPricesSchema(
                payment=MoneySchema(value=3500.0, currencyId="RUR"),
                subsidy=MoneySchema(value=100.0, currencyId="RUR"),
                cashback=MoneySchema(value=50.0, currencyId="RUR"),
            ),
            delivery=DeliveryOrderDatesSchema(shipment=None),
        )


async def _resolve_db_url() -> str:
    """Возвращает tenant-URL пользователя test_user или пропускает тест."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.username == TEST_USERNAME)
        )
        user = result.scalar_one_or_none()

    if user is None:
        pytest.skip(
            f"Пользователь '{TEST_USERNAME}' не найден. "
            "Создай его через: make create-user"
        )
    return user.database_url


@pytest_asyncio.fixture
async def client():
    """Поднимает HTTP-клиент с подменой маркет-клиента и tenant-сессии.

    - get_market_client_obj → FakeMarketClient (без реального API);
    - get_db → сессия к tenant-БД test_user (без JWT);
    - перед тестом очищает orders/order_items для изоляции.
    """
    db_url = await _resolve_db_url()

    # Убеждаемся, что таблицы tenant-БД существуют, и очищаем заказы.
    provisioner = Provisioner()
    db_name = db_url.rstrip("/").split("/")[-1]
    try:
        await provisioner.create_tenant_database(db_name=db_name)
    except Exception:
        pass

    engine = create_async_engine(db_url, echo=False)
    try:
        async with engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
            await conn.execute(text("DELETE FROM order_items"))
            await conn.execute(text("DELETE FROM orders"))
            await conn.commit()
    finally:
        await engine.dispose()

    app.dependency_overrides[get_market_client_obj] = lambda: FakeMarketClient()

    async def _override_get_db():
        session_maker = get_sessionmaker(db_url)
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_notification_lifecycle_and_returns(client):
    """Прогоняет все типы уведомлений и проверяет GET /returns + GET /orders."""
    now = datetime.now(timezone.utc).isoformat()

    # --- ORDER_CREATED ------------------------------------------------------
    for oid in ORDER_IDS:
        resp = await client.post(
            "/notification",
            json={
                "notificationType": "ORDER_CREATED",
                "orderId": oid,
                "campaignId": 100500,
                "createdAt": now,
                "items": [
                    {"offerId": f"SKU-{oid}-A", "count": 2},
                    {"offerId": f"SKU-{oid}-B", "count": 1},
                ],
            },
        )
        assert resp.status_code == 200

    # --- ORDER_STATUS_UPDATED ----------------------------------------------
    resp = await client.post(
        "/notification",
        json={
            "notificationType": "ORDER_STATUS_UPDATED",
            "orderId": 999001,
            "campaignId": 100500,
            "status": "DELIVERED",
            "updatedAt": now,
        },
    )
    assert resp.status_code == 200

    # --- ORDER_CANCELLED ---------------------------------------------------
    resp = await client.post(
        "/notification",
        json={
            "notificationType": "ORDER_CANCELLED",
            "orderId": 999002,
            "campaignId": 100500,
            "cancelledAt": now,
            "items": [
                {"offerId": "SKU-999002-A", "count": 2},
                {"offerId": "SKU-999002-B", "count": 1},
            ],
        },
    )
    assert resp.status_code == 200

    # --- ORDER_RETURN_CREATED: RETURN (частичный возврат товара A) ---------
    resp = await client.post(
        "/notification",
        json={
            "notificationType": "ORDER_RETURN_CREATED",
            "orderId": 999003,
            "campaignId": 100500,
            "returnId": 4001,
            "returnType": "RETURN",
            "createdAt": now,
            "items": [{"offerId": "SKU-999003-A", "count": 1}],
        },
    )
    assert resp.status_code == 200

    # --- ORDER_RETURN_CREATED: UNREDEEMED (невыкуп товара B) ---------------
    resp = await client.post(
        "/notification",
        json={
            "notificationType": "ORDER_RETURN_CREATED",
            "orderId": 999004,
            "campaignId": 100500,
            "returnId": 4002,
            "returnType": "UNREDEEMED",
            "createdAt": now,
            "items": [{"offerId": "SKU-999004-B", "count": 1}],
        },
    )
    assert resp.status_code == 200

    # --- GET /returns ------------------------------------------------------
    resp = await client.get("/returns")
    assert resp.status_code == 200
    body = resp.json()

    cancellations = body["cancellations"]
    assert any(o["order_id"] == 999002 and o["is_cancelled"] for o in cancellations)

    returns = body["returns"]
    returned_by_order = {item["order_id"]: item for item in returns}
    assert 999003 in returned_by_order
    assert 999004 in returned_by_order
    assert returned_by_order[999003]["return_type"] == "RETURN"
    assert returned_by_order[999004]["return_type"] == "UNREDEEMED"
    # У возвращённых товаров должно быть проставлено возвращённое количество.
    for item in returns:
        assert (item["returned_count"] or 0) > 0

    # --- GET /orders?day=today ---------------------------------------------
    today = datetime.now(timezone.utc).date().isoformat()
    resp = await client.get(f"/orders?day={today}")
    assert resp.status_code == 200
    orders = resp.json()["orders"]

    by_id = {o["order_id"]: o for o in orders}
    assert by_id[999001]["status"] == "DELIVERED"
    assert by_id[999002]["is_cancelled"] is True
    assert by_id[999003]["has_returned"] is True
    assert by_id[999004]["has_returned"] is True
