"""
Фикстуры для интеграционных тестов с реальным PostgreSQL.

Перед запуском тестов необходимо поднять тестовую БД:

    docker compose up -d test_postgres

URL тестовой БД: postgresql+asyncpg://osman:osman@localhost:5433/system_meta
"""

import asyncio
import uuid
from typing import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Используем тестовый PostgreSQL на порту 5433
TEST_DB_URL = "postgresql+asyncpg://osman:osman@localhost:5433/system_meta"
TEST_POSTGRES_DSN_BASE = "postgresql+asyncpg://osman:osman@localhost:5433"

from app.infrastructure.database import Base


def _unique_db_name() -> str:
    """Генерирует уникальное имя tenant-базы для изоляции тестов."""
    return f"test_tenant_{uuid.uuid4().hex[:12]}"


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """Создаёт движок к системной БД тестового PostgreSQL."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def system_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Сессия к системной БД (system_meta)."""
    async with test_engine.connect() as conn:
        # Убеждаемся что таблицы system_meta существуют
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    maker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def tenant_db(
    system_session: AsyncSession,
) -> AsyncIterator[str]:
    """
    Создаёт изолированную tenant-базу, накатывает миграции и возвращает её URL.
    После теста база удаляется.
    """
    db_name = _unique_db_name()
    tenant_url = f"{TEST_POSTGRES_DSN_BASE}/{db_name}"

    # Создаём физическую БД
    admin_url = f"{TEST_POSTGRES_DSN_BASE}/postgres"
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        async with admin_engine.connect() as conn:
            await conn.execute(text(f'CREATE DATABASE "{db_name}" OWNER osman;'))
    finally:
        await admin_engine.dispose()

    # Накатываем таблицы в tenant-базу
    tenant_engine = create_async_engine(tenant_url, echo=False)
    try:
        async with tenant_engine.connect() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
    finally:
        await tenant_engine.dispose()

    yield tenant_url

    # Cleanup: удаляем tenant-базу
    cleanup_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with cleanup_engine.connect() as conn:
            # Отключаем активные подключения
            await conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
                    f"FROM pg_stat_activity "
                    f"WHERE pg_stat_activity.datname = '{db_name}' "
                    f"AND pid <> pg_backend_pid();"
                )
            )
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}";'))
    finally:
        await cleanup_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def tenant_session_factory(tenant_db: str):
    """Возвращает фабрику сессий для tenant-базы."""
    engine = create_async_engine(tenant_db, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield maker
    await engine.dispose()
