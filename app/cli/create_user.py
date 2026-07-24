import asyncio
from getpass import getpass

from app.auth.repositories.auth_repo import AuthRepository
from app.auth.schemas.user_schemas import RegisterUserSchema
from app.auth.services.handle_auth import AuthHandler
from app.infrastructure.database import async_session_maker

username: str = input("Username: ")
password: str = getpass("Password: ")


async def create_user(username: str, password: str):
    async with async_session_maker() as session:
        repo = AuthRepository(session)
        service = AuthHandler(repo)

        payload = RegisterUserSchema(
            username=username,
            password=password,
        )

        await service.handle_register_user(payload)


asyncio.run(create_user(username, password))
