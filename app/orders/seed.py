"""
Скрипт для заполнения tenant-БД пользователя тестовыми заказами
в разных статусах (для проверки отображения заказов на фронтенде).

Использование (изнутри Docker-контейнера backend):

    uv run python -m app.orders.seed <username>

Пример:

    docker compose exec backend uv run python -m app.orders.seed test_user

Создаёт 5 заказов и накатывает на них разные типы уведомлений:

    777001 — обычный заказ (PROCESSING, без изменений)
    777002 — ORDER_STATUS_UPDATED → DELIVERED
    777003 — ORDER_CANCELLED (весь заказ отменён)
    777004 — ORDER_RETURN_CREATED returnType=RETURN (частичный возврат товара A)
    777005 — ORDER_RETURN_CREATED returnType=UNREDEEMED (невыкуп товара B)

Скрипт идемпотентен: перед заполнением очищает таблицы orders/order_items
пользователя. Данные ОСТАЮТСЯ в БД — после запуска можно зайти на фронтенд.
"""

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select, text
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
    NotificationReturnItemSchema,
    NotificationType,
    OrderCancelledNotificationSchema,
    OrderCreatedNotificationSchema,
    OrderPricesSchema,
    OrderReturnCreatedNotificationSchema,
    OrderStatusUpdatedNotificationSchema,
    ResponseToMarketSchema,
    ReturnType,
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
    """Заполняет tenant-БД пользователя заказами в разных статусах."""

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

    # 2. Убеждаемся, что таблицы в tenant-БД существуют, и очищаем старые заказы
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
            # Идемпотентность: удаляем старые заказы, чтобы перезапуск давал чистую картину.
            await conn.execute(text("DELETE FROM order_items"))
            await conn.execute(text("DELETE FROM orders"))
            await conn.commit()
        print("   ✅ Таблицы в tenant-БД готовы, старые заказы очищены")
    finally:
        await tenant_engine.dispose()

    # 3. Создаём заказы и накатываем разные типы уведомлений
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

        now = datetime.now(timezone.utc)

        # 3.1 ORDER_CREATED — создаём 5 заказов
        test_orders = [
            (777001, 100500),
            (777002, 100500),
            (777003, 100500),
            (777004, 100501),
            (777005, 100501),
        ]

        for order_id, campaign_id in test_orders:
            notification = OrderCreatedNotificationSchema(
                orderId=order_id,
                campaignId=campaign_id,
                notificationType=NotificationType.ORDER_CREATED,
                items=[
                    NotificationOrderItemSchema(offerId=f"SKU-{order_id}-A", count=2),
                    NotificationOrderItemSchema(offerId=f"SKU-{order_id}-B", count=1),
                ],
                createdAt=now,
            )
            result = await handler.add_order_created(notification)
            print(
                f"   📦 Заказ #{order_id} (campaign={campaign_id}) — "
                f"{'создан' if result == 'ok' else 'уже существует'}"
            )

        # 3.2 ORDER_STATUS_UPDATED — 777002 получает статус DELIVERED
        await handler.update_order_status(
            OrderStatusUpdatedNotificationSchema(
                orderId=777002,
                campaignId=100500,
                notificationType=NotificationType.ORDER_STATUS_UPDATED,
                status="DELIVERED",
                updatedAt=now,
            )
        )
        print("   🔄 Заказ #777002 — статус обновлён до DELIVERED")

        # 3.3 ORDER_CANCELLED — 777003 отменён целиком
        await handler.cancel_order(
            OrderCancelledNotificationSchema(
                orderId=777003,
                campaignId=100500,
                notificationType=NotificationType.ORDER_CANCELLED,
                items=[
                    NotificationOrderItemSchema(offerId="SKU-777003-A", count=2),
                    NotificationOrderItemSchema(offerId="SKU-777003-B", count=1),
                ],
                cancelledAt=now,
            )
        )
        print("   ❌ Заказ #777003 — отменён (ORDER_CANCELLED)")

        # 3.4 ORDER_RETURN_CREATED returnType=RETURN — частичный возврат в 777004
        await handler.create_return_order(
            OrderReturnCreatedNotificationSchema(
                orderId=777004,
                campaignId=100501,
                notificationType=NotificationType.ORDER_RETURN_CREATED,
                returnId=4001,
                returnType=ReturnType.RETURN,
                items=[
                    NotificationReturnItemSchema(offerId="SKU-777004-A", count=1),
                ],
                createdAt=now,
            )
        )
        print("   ↩️  Заказ #777004 — возврат товара A (RETURN)")

        # 3.5 ORDER_RETURN_CREATED returnType=UNREDEEMED — невыкуп в 777005
        await handler.create_return_order(
            OrderReturnCreatedNotificationSchema(
                orderId=777005,
                campaignId=100501,
                notificationType=NotificationType.ORDER_RETURN_CREATED,
                returnId=4002,
                returnType=ReturnType.UNREDEEMED,
                items=[
                    NotificationReturnItemSchema(offerId="SKU-777005-B", count=1),
                ],
                createdAt=now,
            )
        )
        print("   🚫 Заказ #777005 — невыкуп товара B (UNREDEEMED)")

    # 4. Итог
    print()
    print("=" * 60)
    print("🎉  ГОТОВО — заказы в разных статусах созданы!")
    print()
    print("   Теперь заходи на фронтенд:")
    print(f"   Логин: {username}")
    print("   Пароль: 1234")
    print("   Вкладка «📦 Заказы» → выбери сегодняшнюю дату")
    print()
    print("   Что увидишь:")
    print("   #777001 — обычный заказ (PROCESSING)")
    print("   #777002 — DELIVERED (зелёный бейдж)")
    print("   #777003 — Отменён (вся карточка красная)")
    print("   #777004 — «Возврат» внизу, товар A помечен «Возврат»")
    print("   #777005 — «Невыкуп» внизу, товар B помечен «Невыкуп»")
    print("=" * 60)


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
