import asyncio
import sys
from getpass import getpass

# 1. Принудительно устанавливаем UTF-8 кодировку для ввода
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

from app.auth.repo import AuthRepository
from app.auth.schemas import RegisterUserSchema
from app.auth.services import AuthHandler
from app.infrastructure.database import async_session_maker


def safe_input(prompt: str) -> str:
    """Безопасное чтение ввода с очисткой от суррогатных символов."""
    val = input(prompt)
    return val.encode("utf-8", "ignore").decode("utf-8").strip()


async def create_user_action():
    username = safe_input("Username: ")
    password = getpass("Password: ").strip()

    async with async_session_maker() as session:
        repo = AuthRepository(session)
        service = AuthHandler(repo)
        payload = RegisterUserSchema(username=username, password=password)
        await service.handle_register_user(payload)
    print(f"Пользователь '{username}', с паролем {password} создан.")


async def delete_user_action():
    username = safe_input("Username to delete: ")
    confirm = safe_input(f"Удалить '{username}'? (y/N): ")
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

    choice = safe_input("Введите номер (1/2): ")

    if choice == "1":
        asyncio.run(create_user_action())
    elif choice == "2":
        asyncio.run(delete_user_action())
    else:
        print("Неизвестная команда.")


if __name__ == "__main__":
    main()
