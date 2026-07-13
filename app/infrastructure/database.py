import asyncio
import logging
from datetime import date
from typing import AsyncIterator

import jwt
from alembic import command

# Импортируем инструменты Alembic для программного запуска миграций
from alembic.config import Config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """Класс Base для всех ORM моделей."""

    pass


# ---------------------------------------------------------------------------
# Глобальный движок для системной (основной) БД.
# ---------------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Кэши для мультитенантных БД (динамические подключения селлеров)
# ---------------------------------------------------------------------------
_engines: dict[str, AsyncEngine] = {}
_sessionmakers: dict[str, async_sessionmaker[AsyncSession]] = {}
_user_db_urls: dict[str, str] = {}


def get_engine(db_url: str) -> AsyncEngine:
    """Возвращает существующий engine или создаёт новый для конкретного URL."""
    if db_url not in _engines:
        _engines[db_url] = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
        )
    return _engines[db_url]


def get_sessionmaker(db_url: str) -> async_sessionmaker[AsyncSession]:
    """Возвращает фабрику сессий для конкретного URL."""
    if db_url not in _sessionmakers:
        engine_ = get_engine(db_url)
        _sessionmakers[db_url] = async_sessionmaker(
            engine_,
            expire_on_commit=False,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmakers[db_url]


# ---------------------------------------------------------------------------
# АВТОМАТИЗАЦИЯ MULTI-TENANCY: Создание БД и накатывание миграций
# ---------------------------------------------------------------------------


async def create_tenant_database(db_name: str) -> None:
    """
    Физически создает базу данных в PostgreSQL.
    Использует специальное изолированное подключение с выключенными транзакциями.
    """
    # Подключаемся к системной базе 'postgres', чтобы иметь право создавать другие БД
    sys_url = "postgresql+asyncpg://osman:osman@localhost:5432/postgres"
    temp_engine = create_async_engine(sys_url, isolation_level="AUTOCOMMIT")

    async with temp_engine.connect() as conn:
        try:
            # Проверяем, существует ли база, чтобы избежать ошибок дублирования
            check_query = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
            result = await conn.execute(check_query, {"db_name": db_name})
            exists = result.scalar()

            if not exists:
                # Безопасно экранируем имя базы данных штатными средствами SQLAlchemy
                await conn.execute(text(f'CREATE DATABASE "{db_name}" OWNER osman;'))
                logger.info(
                    f"Физическая база данных '{db_name}' успешно создана на сервере."
                )
            else:
                logger.warning(
                    f"База данных '{db_name}' уже существует. Пропускаем создание."
                )
        finally:
            await temp_engine.dispose()


def init_tenant_migrations(tenant_db_url: str) -> None:
    """
    Программный запуск Alembic для новой БД селлера.
    Запускается в синхронном режиме (потоке), так как сам Alembic внутри синхронен.
    """
    try:
        # Указываем путь к вашему файлу alembic.ini
        alembic_cfg = Config("alembic.ini")
        # Динамически подменяем целевой URL на базу нового селлера
        alembic_cfg.set_main_option("sqlalchemy.url", tenant_db_url)

        # Запускаем команду upgrade head с контекстным маркером 'tenant'
        command.upgrade(alembic_cfg, "head", tag="tenant")
        logger.info(f"Миграции Alembic успешно применены к базе: {tenant_db_url}")
    except Exception as e:
        logger.error(f"Ошибка при накатывании миграций Alembic: {e}")
        raise


# ---------------------------------------------------------------------------
# FastAPI Зависимости (Dependencies)
# ---------------------------------------------------------------------------
security = HTTPBearer()


async def get_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AsyncIterator[AsyncSession]:
    """Извлекает JWT токен, находит database_url селлера и открывает сессию к его личной БД."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="В токене отсутствуют данные пользователя (sub)",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен",
        )

    if username in _user_db_urls:
        db_url = _user_db_urls[username]
    else:
        async with async_session_maker() as system_session:
            query = text("SELECT database_url FROM users WHERE username = :username")
            result = await system_session.execute(query, {"username": username})
            db_url = result.scalar_one_or_none()

            if not db_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Для данного пользователя не настроена база данных",
                )

            # Валидация строки, чтобы бэкенд аварийно не падал из-за записей вроде "string"
            if not str(db_url).startswith("postgresql"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У пользователя указан некорректный формат URL базы данных.",
                )

            _user_db_urls[username] = db_url

    SessionLocal = get_sessionmaker(db_url)
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_system_db() -> AsyncIterator[AsyncSession]:
    """Открывает сессию к центральной БД (для регистрации и логина)."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_db() -> None:
    """Закрывает все соединения при shutdown сервера."""
    for e in _engines.values():
        await e.dispose()
    _engines.clear()
    _sessionmakers.clear()
    _user_db_urls.clear()

    await engine.dispose()
    logger.info("All database connections disposed")
