import asyncio

from sqlalchemy import text

# Импортируем Provisioner и фабрику сессий
from app.infrastructure.database import Provisioner, async_session_maker


async def migrate_all():
    provisioner = Provisioner()

    # 1. Запрашиваем URL баз всех существующих пользователей из центральной БД
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT database_url FROM users"))
        urls = result.scalars().all()

    # 2. Проходим циклом по каждой базе данных и обновляем её до 'head'
    for url in urls:
        if url and str(url).startswith("postgresql"):
            print(f"Обновление базы данных: {url}")
            # Вызываем метод экземпляра Provisioner в отдельном синхронном потоке
            await asyncio.to_thread(provisioner.init_tenant_migrations, url)

    print("Все базы данных пользователей успешно обновлены!")


if __name__ == "__main__":
    asyncio.run(migrate_all())
