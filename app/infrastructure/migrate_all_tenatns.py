# scripts/migrate_all_tenants.py
import asyncio

from sqlalchemy import text

from app.infrastructure.database import async_session_maker, init_tenant_migrations


async def migrate_all():
    # 1. Запрашиваем URL баз всех существующих пользователей из центральной БД
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT database_url FROM users"))
        urls = result.scalars().all()

    # 2. Проходим циклом по каждой базе данных и обновляем её до 'head'
    for url in urls:
        if url and url.startswith("postgresql"):
            print(f"Обновление базы данных: {url}")
            # Выполняем синхронный Alembic в отдельном потоке для каждой БД
            await asyncio.to_thread(init_tenant_migrations, url)

    print("Все базы данных пользователей успешно обновлены!")


if __name__ == "__main__":
    asyncio.run(migrate_all())
