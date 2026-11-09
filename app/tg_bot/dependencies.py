from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_system_db
from app.tg_bot.repo import TelegramBotRepository


async def get_user_repo_obj(session: AsyncSession = Depends(get_system_db)):
    repo = TelegramBotRepository(session)

    return repo
