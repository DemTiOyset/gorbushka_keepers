import asyncio
import sys
from getpass import getpass

from app.auth.repo import AuthRepository
from app.auth.schemas import DeleteUserSchema, RegisterUserSchema
from app.auth.services import AuthHandler
from app.infrastructure.database import async_session_maker


async def create_user_action():
    username = input("Username: ")
    password = getpass("Password: ")

    async with async_session_maker() as session:
        repo = AuthRepository(session)
        service = AuthHandler(repo)
        payload = RegisterUserSchema(username=username, password=password)
        await service.handle_register_user(payload)
    print(f"Пользователь '{username}' создан.")


async def delete_user_action():
    username = input("Username to delete: ")
    confirm = input(f"Удалить '{username}'? (y/N): ")
    if confirm.lower() != "y":
        print("Отмена.")
        return

    async with async_session_maker() as session:
        repo = AuthRepository(session)
        service = AuthHandler(repo)
        await service.handle_delete_user(username=username)
    print(f"Пользователь '{username}' удален.")


def main():
    print("Выберите действие:")
    print("1. Создать пользователя")
    print("2. Удалить пользователя")

    choice = input("Ведите номер (1/2): ").strip()

    if choice == "1":
        asyncio.run(create_user_action())
    elif choice == "2":
        asyncio.run(delete_user_action())
    else:
        print("Неизвестная команда.")


if __name__ == "__main__":
    main()
