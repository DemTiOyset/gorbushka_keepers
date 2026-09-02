"""
Скрипт для заполнения tenant-БД пользователя тестовыми заказами.

Использование (изнутри Docker-контейнера backend):

    uv run python -m app.orders.seed <username>

Пример:

    docker compose exec backend uv run python -m app.orders.seed test_user

Создаёт 3 тестовых заказа (777001, 777002, 777003) с товарами.
Данные ОСТАЮТСЯ в основной БД — после запуска можно зайти на фронтенд.
"""

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database import (
    Base,
    Provisioner,
    TenantSessionManager,
    async_session_maker,
)
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

# ─────────────────────────────────────────────────────────────────────────────
# FakeMarketClient — генерирует тестовые данные вместо запроса к API Яндекса
# ─────────────────────────────────────────────────────────────────────────────


class FakeMarketClient:
    """Для каждого order_id генерирует заказ с двумя товарами."""

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


# ─────────────────────────────────────────────────────────────────────────────
# Основная логика
# ─────────────────────────────────────────────────────────────────────────────


async def seed_orders(username: str):
    """Заполняет tenant-БД пользователя тремя тестовыми заказами."""

    print(f"\n🔍 Ищу пользователя '{username}' в system_meta...")

    # 1. Находим пользователя
    async with async_session_maker() as system_session:
        result = await system_session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if user is None:
            print(f"❌ Пользователь '{username}' не найден.")
            print(
                "   Создай его через: docker compose exec backend uv run python -m app.auth.cli"
            )
            return

        if not user.api_key or not user.business_id or not user.campaign_ids:
            print(f"❌ У пользователя '{username}' не заполнены данные магазина.")
            print(
                "   Привяжи магазин через: docker compose exec backend uv run python -m app.users.cli"
            )
            return

        db_url = user.database_url
        print(f"   ✅ Пользователь найден: {username}")
        print(f"   tenant-БД: {db_url}")
        print(f"   business_id: {user.business_id}")
        print(f"   campaign_ids: {user.campaign_ids}")

    # 2. Убеждаемся, что таблицы в tenant-БД существуют
    provisioner = Provisioner()
    db_name = db_url.rstrip("/").split("/")[-1]

    try:
        await provisioner.create_tenant_database(db_name=db_name)
    except Exception:
        pass  # БД уже существует

    tenant_engine = create_async_engine(db_url, echo=False)
    try:
        async with tenant_engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
        print("   ✅ Таблицы в tenant-БД готовы")
    finally:
        await tenant_engine.dispose()

    # 3. Создаём 3 заказа через add_order_created
    fake_client = FakeMarketClient()
    tenant_manager = TenantSessionManager()

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
        skipped_count = 0

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
                skipped_count += 1

    # 4. Итог
    print()
    print("=" * 55)
    print(f"🎉  ГОТОВО — создано {created_count} заказов (пропущено: {skipped_count})")
    print()
    print("   Теперь заходи на фронтенд:")
    print(f"   Логин: {username}")
    print("   Пароль: 1234")
    print("   Вкладка «📦 Заказы» → выбери сегодняшнюю дату")
    print("=" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# CLI-вход
# ─────────────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print("Использование: python -m app.orders.seed <username>")
        print("Пример:     python -m app.orders.seed test_user")
        sys.exit(1)

    username = sys.argv[1]
    asyncio.run(seed_orders(username))


if __name__ == "__main__":
    main()
