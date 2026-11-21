from app.users.exceptions import StoreAlreadyExistError, TelegramDataAlreadyExist
from app.users.repo import UserRepositoryInterface
from app.users.schemas import StoreDataResponse, StoreDataSchema, TelegramDataResponse


class UserHandler:
    def __init__(self, repo: UserRepositoryInterface):
        self.repo = repo

    async def create_store(self, store_data: StoreDataSchema):
        store_from_db = await self.repo.get_user_by_business_id_or_none(
            store_data.business_id
        )

        if store_from_db:
            raise StoreAlreadyExistError

        created_store_from_db = await self.repo.create_user_store(
            username=store_data.username, store_data=store_data.model_dump()
        )

        store = StoreDataResponse.model_validate(created_store_from_db)

        await self.repo.commit()

        return store

    async def create_telegram_id(self, telegram_id: int, username: str):
        user_from_db = await self.repo.get_user_by_telegram_id(telegram_id=telegram_id)

        if user_from_db:
            raise TelegramDataAlreadyExist

        created_telegram_data_from_db = await self.repo.create_telegram_data(
            telegram_id=telegram_id, username=username
        )

        telegram_data = TelegramDataResponse.model_validate(
            created_telegram_data_from_db
        )

        await self.repo.commit()

        return telegram_data
