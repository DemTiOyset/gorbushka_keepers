from app.users.exceptions import StoreAlreadyExistError
from app.users.repo import UserRepositoryInfrastructure
from app.users.schemas import StoreDataResponse, StoreDataSchema


class UserHandler:
    def __init__(self, repo: UserRepositoryInfrastructure):
        self.repo = repo

    async def create_store(self, store_data: StoreDataSchema):
        store_from_db = await self.repo.get_user_by_business_id_or_none(
            store_data.business_id
        )

        if store_from_db:
            raise StoreAlreadyExistError

        store_from_db = await self.repo.create_user_store(
            username=store_data.username, store_data=store_data.model_dump()
        )

        store = StoreDataResponse.model_validate(store_from_db)

        await self.repo.commit()

        return store
