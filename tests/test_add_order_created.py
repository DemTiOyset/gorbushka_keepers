"""
Интеграционный тест для OrderNotificationHandler.add_order_created.

Заполняет ОСНОВНУЮ БД (system_meta + tenant-базу) тестовыми данными.
После прогона можно сразу зайти на фронтенд и увидеть заказы.

ЗАПУСК (внутри Docker-контейнера backend):

    docker compose exec backend uv run pytest tests/test_add_order_created.py -v -s

Перед запуском ДОЛЖЕН существовать пользователь с campaign_id=100500.
Создай его через CLI:

    docker compose exec backend uv run python -m app.auth.cli       # создать юзера test_user / 1234
    docker compose exec backend uv run python -m app.users.cli       # привязать магазин
        Юзернейм: test_user
        API ключ: test-api-key
        Business ID: 123456
        Campaign ids: 100500 100501

FakeMarketClient подменяет реальный API Яндекса — генерирует тестовые заказы.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import (
    Base,
    Provisioner,
    TenantSessionManager,
    async_session_maker,
)
from app.infrastructure.models.order import Order
from app.infrastructure.models.user import User
from app.orders.repo import OrdersRepository
from app.orders.schemas import (
    BusinessOrderItemSchema,
    BusinessOrderSchema,
    DeliveryOrderDatesSchema,
    ItemPricesSchema,
    MoneySchema,
    NotificationOrderItemSchema,
    NotificationType,
    OrderCreatedNotificationSchema,
    OrderPricesSchema,
    ResponseToMarketSchema,
)
from app.orders.services import OrderNotificationHandler
from app.users.repo import UserRepository

# =========================================================================
# FakeMarketClient — вместо реального API Яндекса возвращает тестовые данные
# =========================================================================


class FakeMarketClient:
    """
    Для каждого order_id генерирует заказ с двумя товарами.
    expected_payout = cashback(50) + payment(3500) + subsidy(100) = 3650.
    """

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
                    offerName=f"Тестовый товар A (заказ #{oid})",
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
                    offerName=f"Тестовый товар B (заказ #{oid})",
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


# =========================================================================
# Тесты
# =========================================================================

TEST_USERNAME = "test_user"


@pytest.mark.asyncio
async def test_add_order_created_seeds_three_orders():
    """
    Создаёт 3 заказа через add_order_created в tenant-БД пользователя test_user.
    Данные ОСТАЮТСЯ в БД после теста — заходи на фронтенд и смотри.
    """

    # ------------------------------------------------------------------
    # 1. Находим test_user в системной БД
    # ------------------------------------------------------------------
    async with async_session_maker() as system_session:
        result = await system_session.execute(
            select(User).where(User.username == TEST_USERNAME)
        )
        user = result.scalar_one_or_none()

        if user is None:
            pytest.skip(
                f"Пользователь '{TEST_USERNAME}' не найден. "
                "Создай его через CLI: "
                "docker compose exec backend uv run python -m app.auth.cli"
            )

        if not user.api_key or not user.business_id or not user.campaign_ids:
            pytest.skip(
                f"У пользователя '{TEST_USERNAME}' не заполнены данные магазина. "
                "Привяжи магазин через CLI: "
                "docker compose exec backend uv run python -m app.users.cli"
            )

        db_url = user.database_url
        print(f"\n✅ Найден пользователь: {TEST_USERNAME}")
        print(f"   tenant-БД: {db_url}")
        print(f"   business_id: {user.business_id}")
        print(f"   campaign_ids: {user.campaign_ids}")

    # ------------------------------------------------------------------
    # 2. Убеждаемся, что таблицы в tenant-БД существуют (накатываем если нет)
    # ------------------------------------------------------------------
    provisioner = Provisioner()
    db_name = db_url.rstrip("/").split("/")[-1]

    try:
        await provisioner.create_tenant_database(db_name=db_name)
    except Exception:
        pass  # БД уже существует — ок

    from sqlalchemy.ext.asyncio import create_async_engine

    tenant_engine = create_async_engine(db_url, echo=False)
    try:
        async with tenant_engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
        print("   ✅ Таблицы в tenant-БД готовы")
    finally:
        await tenant_engine.dispose()

    # ------------------------------------------------------------------
    # 3. Создаём 3 заказа через add_order_created (с FakeMarketClient)
    # ------------------------------------------------------------------
    fake_client = FakeMarketClient()
    tenant_manager = TenantSessionManager()

    # Используем РЕАЛЬНЫЙ UserRepository для поиска пользователя по campaign_id
    async with async_session_maker() as system_session:
        user_repo = UserRepository(system_session)

        handler = OrderNotificationHandler(
            tenant_manager=tenant_manager,  # pyright: ignore[reportArgumentType]
            user_repo=user_repo,  # pyright: ignore[reportArgumentType]
            market_client=fake_client,  # pyright: ignore[reportArgumentType]
            order_repo_type=OrdersRepository,  # pyright: ignore[reportArgumentType]
        )

        test_orders = [
            (777001, 100500),
            (777002, 100500),
            (777003, 100501),
        ]

        created_count = 0
        for order_id, campaign_id in test_orders:
            notification = OrderCreatedNotificationSchema(
                orderId=order_id,
                campaignId=campaign_id,
                notificationType=NotificationType.ORDER_CREATED,
                items=[
                    NotificationOrderItemSchema(offerId=f"SKU-{order_id}-A", count=2),
                    NotificationOrderItemSchema(offerId=f"SKU-{order_id}-B", count=1),
                ],
                createdAt=datetime.now(timezone.utc),
            )

            result = await handler.add_order_created(notification)

            if result == "ok":
                print(f"   📦 Заказ #{order_id} (campaign={campaign_id}) — создан")
                created_count += 1
            elif result is None:
                print(f"   ⏭️  Заказ #{order_id} — уже существует, пропущен")

        print(f"\n   Создано новых заказов: {created_count}")

    # ------------------------------------------------------------------
    # 4. Проверяем заказы в tenant-БД
    # ------------------------------------------------------------------
    from sqlalchemy.ext.asyncio import async_sessionmaker as maker
    from sqlalchemy.orm import selectinload

    tenant_maker = maker(
        create_async_engine(db_url, echo=False),
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with tenant_maker() as tenant_session:
        for order_id, campaign_id in test_orders:
            stmt = (
                select(Order)
                .where(Order.order_id == order_id)
                .options(selectinload(Order.items))
            )
            result = await tenant_session.execute(stmt)
            order = result.scalar_one_or_none()

            assert order is not None, (
                f"Заказ #{order_id} должен существовать в tenant-БД"
            )
            assert order.campaign_id == campaign_id
            assert order.status == "PROCESSING"
            assert float(order.expected_payout) == 3650.0
            assert len(order.items) == 2

            item_ids = {it.offer_id for it in order.items}
            assert f"SKU-{order_id}-A" in item_ids
            assert f"SKU-{order_id}-B" in item_ids

            print(f"   ✅ Заказ #{order_id} проверен: 2 товара, payout=3650.00 ₽")

    # ------------------------------------------------------------------
    # 5. Итог
    # ------------------------------------------------------------------
    print()
    print("=" * 55)
    print("🎉  ТЕСТ ПРОЙДЕН — все 3 заказа в БД!")
    print()
    print("   Теперь заходи на фронтенд:")
    print(f"   Логин: {TEST_USERNAME}")
    print("   Пароль: 1234")
    print("   Вкладка «📦 Заказы» → выбери сегодняшнюю дату")
    print("=" * 55)
