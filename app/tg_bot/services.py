import logging

from app.infrastructure.database import (
    TenantSessionManagerInterface,
)
from app.tg_bot.repo import TelegramBotRepositoryInterface
from app.users.repo import UserRepositoryInterface

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    def __init__(
        self,
        tenant_manager: TenantSessionManagerInterface,
        user_repo: UserRepositoryInterface,
        telegram_bot_repo_type: TelegramBotRepositoryInterface,
    ):
        self.tenant_manager = tenant_manager
        self.user_repo = user_repo
        self.telegram_bot_repo_type = telegram_bot_repo_type

    async def get_all_pending_returns(self, telegram_id: int) -> list[dict] | None:
        """
        Находит все возвраты по всем магазинам/пользователям,
        которые ещё не пришли к продавцу (is_returned_finished == False).
        """
        pending_returns = []

        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.telegram_bot_repo_type,  # pyright: ignore[reportArgumentType]
        ) as telegram_bot_repo:
            items = telegram_bot_repo.get_returned_orders()

            for item in items:
                pending_returns.append(
                    {
                        "username": user_from_db.username,
                        "database_url": user_from_db.database_url,
                        "item_id": item.id,
                        "order_id": item.order_id,
                        "offer_id": item.offer_id,
                        "offer_name": item.offer_name,
                        "returned_count": item.returned_count or 1,
                        "return_type": item.return_type or "RETURN",
                        "is_returned_finished": item.is_returned_finished,
                    }
                )

        return pending_returns

    async def set_return_status(
        self, telegram_id, item_id: int, is_finished: bool
    ) -> bool | None:
        """
        Обновляет статус возврата товара (is_returned_finished).
        Ищет товар по item_id в tenant-базах пользователей.
        """
        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.telegram_bot_repo_type,  # pyright: ignore[reportArgumentType]
        ) as telegram_bot_repo:
            order_item = telegram_bot_repo.get_order_item(item_id)

            if order_item is not None:
                order_item.is_returned_finished = is_finished
                telegram_bot_repo.commit()
                return True

        return False

    async def get_return_by_id(self, telegram_id: int, item_id: int) -> dict | None:
        """Получает детальную информацию о возврате по id товара."""
        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.telegram_bot_repo_type,  # pyright: ignore[reportArgumentType]
        ) as telegram_bot_repo:
            order_item = telegram_bot_repo.get_order_item(item_id)

            if order_item is not None:
                return {
                    "username": user_from_db.username,
                    "item_id": order_item.id,
                    "order_id": order_item.order_id,
                    "offer_id": order_item.offer_id,
                    "offer_name": order_item.offer_name,
                    "returned_count": order_item.returned_count or 1,
                    "return_type": order_item.return_type or "RETURN",
                    "is_returned_finished": order_item.is_returned_finished,
                }

        return
