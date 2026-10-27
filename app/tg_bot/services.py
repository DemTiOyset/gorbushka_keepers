import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.infrastructure.config import settings
from app.infrastructure.database import async_session_maker
from app.infrastructure.models.user import User
from app.infrastructure.models.order_item import OrderItem

logger = logging.getLogger(__name__)


async def get_all_pending_returns() -> list[dict]:
    """
    Находит все возвраты по всем магазинам/пользователям,
    которые ещё не пришли к продавцу (is_returned_finished == False).
    """
    pending_returns = []

    async with async_session_maker() as system_session:
        result = await system_session.execute(select(User))
        users = result.scalars().all()

    for user in users:
        if not user.database_url:
            continue

        tenant_engine = create_async_engine(user.database_url, echo=False)
        tenant_session_factory = async_sessionmaker(tenant_engine, expire_on_commit=False)

        try:
            async with tenant_session_factory() as session:
                stmt = select(OrderItem).where(
                    OrderItem.returned_count > 0,
                    OrderItem.is_returned_finished.is_(False),
                )
                res = await session.execute(stmt)
                items = res.scalars().all()

                for item in items:
                    pending_returns.append({
                        "username": user.username,
                        "database_url": user.database_url,
                        "item_id": item.id,
                        "order_id": item.order_id,
                        "offer_id": item.offer_id,
                        "offer_name": item.offer_name,
                        "returned_count": item.returned_count or 1,
                        "return_type": item.return_type or "RETURN",
                        "is_returned_finished": item.is_returned_finished,
                    })
        except Exception as e:
            logger.error(f"Error fetching pending returns for user {user.username}: {e}")
        finally:
            await tenant_engine.dispose()

    return pending_returns


async def set_return_status(item_id: int, is_finished: bool) -> bool:
    """
    Обновляет статус возврата товара (is_returned_finished).
    Ищет товар по item_id в tenant-базах пользователей.
    """
    async with async_session_maker() as system_session:
        result = await system_session.execute(select(User))
        users = result.scalars().all()

    for user in users:
        if not user.database_url:
            continue

        tenant_engine = create_async_engine(user.database_url, echo=False)
        tenant_session_factory = async_sessionmaker(tenant_engine, expire_on_commit=False)

        try:
            async with tenant_session_factory() as session:
                stmt = select(OrderItem).where(OrderItem.id == item_id)
                res = await session.execute(stmt)
                order_item = res.scalar_one_or_none()

                if order_item is not None:
                    order_item.is_returned_finished = is_finished
                    await session.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating return status for item {item_id}: {e}")
        finally:
            await tenant_engine.dispose()

    return False


async def get_return_by_id(item_id: int) -> dict | None:
    """Получает детальную информацию о возврате по id товара."""
    async with async_session_maker() as system_session:
        result = await system_session.execute(select(User))
        users = result.scalars().all()

    for user in users:
        if not user.database_url:
            continue

        tenant_engine = create_async_engine(user.database_url, echo=False)
        tenant_session_factory = async_sessionmaker(tenant_engine, expire_on_commit=False)

        try:
            async with tenant_session_factory() as session:
                stmt = select(OrderItem).where(OrderItem.id == item_id)
                res = await session.execute(stmt)
                item = res.scalar_one_or_none()

                if item is not None:
                    return {
                        "username": user.username,
                        "item_id": item.id,
                        "order_id": item.order_id,
                        "offer_id": item.offer_id,
                        "offer_name": item.offer_name,
                        "returned_count": item.returned_count or 1,
                        "return_type": item.return_type or "RETURN",
                        "is_returned_finished": item.is_returned_finished,
                    }
        except Exception as e:
            logger.error(f"Error finding return item {item_id}: {e}")
        finally:
            await tenant_engine.dispose()

    return None
