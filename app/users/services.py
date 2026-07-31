from app.users.repo import UserRepositoryInfrastructure
from app.users.schemas import StoreDataDTO


class UserHandler:
    def __init__(self, repo: UserRepositoryInfrastructure):
        self.repo = repo

    async def create_store(self, store_data: StoreDataDTO): ...
