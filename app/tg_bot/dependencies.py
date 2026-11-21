from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import TenantSessionManager, async_session_maker
from app.tg_bot.repo import TelegramBotRepository
from app.tg_bot.services import TelegramBotHandler
from app.users.repo import UserRepository


async def get_user_repo_obj(session: AsyncSession):
    repo = UserRepository(session)

    return repo


async def get_service():
    async with async_session_maker() as session:
        user_repo = await get_user_repo_obj(session)

    handler_obj = TelegramBotHandler(
        user_repo=user_repo,  # pyright: ignore[reportArgumentType]
        tenant_manager=TenantSessionManager,  # pyright: ignore[reportArgumentType]
        telegram_bot_repo_type=TelegramBotRepository,  # pyright: ignore[reportArgumentType]
    )

    return handler_obj
