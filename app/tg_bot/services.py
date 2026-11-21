import logging

from app.infrastructure.database import (
    TenantSessionManagerInterface,
)
from app.tg_bot.exceptions import UserIsNotExist
from app.tg_bot.repo import TelegramBotRepositoryInterface
from app.tg_bot.schemas import (
    BaseRequest,
    GetOrderRequest,
    OrderItemResponse,
    SetStatusRequest,
)
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

    async def get_user_from_db(self, telegram_id):
        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)
        return user_from_db

    async def get_all_pending_returns(
        self, telegram_id: int | None
    ) -> list[OrderItemResponse] | None:
        """
        Находит все возвраты по всем магазинам/пользователям,
        которые ещё не пришли к продавцу (is_returned_finished == False).
        """
        pending_returns: list[OrderItemResponse] = []

        if telegram_id is None:
            return

        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)

        if user_from_db is None:
            raise UserIsNotExist

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.telegram_bot_repo_type,  # pyright: ignore[reportArgumentType]
        ) as telegram_bot_repo:
            items = telegram_bot_repo.get_returned_orders()

            for item in items:
                order_item_schema = OrderItemResponse(
                    username=user_from_db.username,
                    item_id=item.id,
                    order_id=item.order_id,
                    offer_id=item.offer_id,
                    offer_name=item.offer_name,
                    returned_count=item.returned_count,
                    return_type=item.return_type,
                    is_returned_finished=item.is_returned_finished,
                )
                pending_returns.append(order_item_schema)

        return pending_returns

    async def set_return_status(
        self, telegram_id: int | None, item_id: int, is_finished: bool = False
    ) -> bool | None:
        """
        Обновляет статус возврата товара (is_returned_finished).
        Ищет товар по item_id в tenant-базах пользователей.
        """
        if telegram_id is None:
            return

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

    async def get_return_by_id(
        self,
        item_id: int,
        telegram_id: int | None,
    ) -> OrderItemResponse | None:
        """Получает детальную информацию о возврате по id товара."""
        if telegram_id is None:
            return
        user_from_db = await self.user_repo.get_user_by_telegram_id(telegram_id)

        if user_from_db is None:
            return

        async with self.tenant_manager.get_repository(  # pyright: ignore[reportGeneralTypeIssues]
            user_from_db.database_url,
            self.telegram_bot_repo_type,  # pyright: ignore[reportArgumentType]
        ) as telegram_bot_repo:
            item = telegram_bot_repo.get_order_item(item_id)

            if item is not None:
                order_item_schema = OrderItemResponse(
                    username=user_from_db.username,
                    item_id=item.id,
                    order_id=item.order_id,
                    offer_id=item.offer_id,
                    offer_name=item.offer_name,
                    returned_count=item.returned_count,
                    return_type=item.return_type,
                    is_returned_finished=item.is_returned_finished,
                )

                return order_item_schema

        return
