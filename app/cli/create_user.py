import asyncio
from getpass import getpass

from app.auth.repositories.dependencies import get_repo_obj
from app.auth.schemas.user_schemas import RegisterUserSchema
from app.auth.services.handle_auth import AuthHandler

username: str = input("Username: ")
password: str = getpass("Password: ")


async def create_user(username: str, password: str):
    repo = await get_repo_obj()
    service = AuthHandler(repo)
    payload = RegisterUserSchema(username=username, password=password)

    await service.handle_register_user(payload)

    return {"Message": "User Created Succesfully."}


asyncio.run(create_user(username, password))
