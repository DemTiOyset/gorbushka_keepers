import asyncio
import sys

from app.infrastructure.database import async_session_maker
from app.users.repo import UserRepository
from app.users.schemas import StoreDataSchema
from app.users.services import UserHandler

# 1. Принудительно устанавливаем UTF-8 кодировку для ввода
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")


def safe_input(prompt: str) -> str:
    """Безопасное чтение ввода с очисткой от суррогатных символов."""
    val = input(prompt)
    return val.encode("utf-8", "ignore").decode("utf-8").strip()


async def create_store_action():
    username = safe_input("Юзернейм в системе Dozor:")
    market_type = "yandex"
    api_key = safe_input("API ключ с маркета:")
    business_id = safe_input("Business ID с маркета:")
    campaign_ids = list(map(int, safe_input("Campaign ids:").split()))

    store_data = StoreDataSchema(
        username=username,
        market_type=market_type,
        api_key=api_key,
        business_id=business_id,
        campaign_ids=campaign_ids,
    )
    async with async_session_maker() as session:
        repo = UserRepository(session)
        service = UserHandler(repo=repo)  # pyright: ignore[reportArgumentType]
        await service.create_store(store_data=store_data)
    print(f"Магазин для пользователя {username} в маркете {market_type}")


def main():
    print("Выберите действие:")
    print("1. Создать данные о магазине.")

    choice = safe_input("Введите номер (1): ")

    if choice == "1":
        asyncio.run(create_store_action())
    else:
        print("Неизвестная команда.")


if __name__ == "__main__":
    main()
