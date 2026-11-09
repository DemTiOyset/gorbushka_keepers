import sys

from app.infrastructure.database import async_session_maker
from app.tg_bot.repo import TelegramBotRepository

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore[reportAttributeAccessIssue]


def safe_input(prompt: str) -> str:
    """Безопасное чтение ввода с очисткой от суррогатных символов."""
    val = input(prompt)
    return val.encode("utf-8", "ignore").decode("utf-8").strip()


async def create_user_telegram_id():
    username = input()
    telegram_id = int(input())

    async with async_session_maker() as session:
        repo = TelegramBotRepository(session)
        service = UserHandler(repo=repo)  # pyright: ignore[reportArgumentType]
        await service.create_store()
    print(f"Telegram id для пользователя {username}")
