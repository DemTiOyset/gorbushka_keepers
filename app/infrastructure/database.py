import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Protocol, Type, TypeVar

import jwt
from alembic import command
from alembic.config import Config
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
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
class ProvisionerInterface(Protocol):
    async def create_tenant_database(self, db_name: str) -> None: ...

    def init_tenant_migrations(self, tenant_db_url: str) -> None: ...


class Provisioner:
    async def create_tenant_database(self, db_name: str) -> None:
        """
        Физически создает базу данных в PostgreSQL.
        Использует специальное изолированное подключение с выключенными транзакциями.
        """
        sys_url = settings.postgres_admin_url
        temp_engine = create_async_engine(sys_url, isolation_level="AUTOCOMMIT")

        async with temp_engine.connect() as conn:
            try:
                check_query = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
                result = await conn.execute(check_query, {"db_name": db_name})
                exists = result.scalar()

                if not exists:
                    await conn.execute(
                        text(f'CREATE DATABASE "{db_name}" OWNER osman;')
                    )
                    logger.info(
                        f"Физическая база данных '{db_name}' успешно создана на сервере."
                    )
                else:
                    logger.warning(
                        f"База данных '{db_name}' уже существует. Пропускаем создание."
                    )
            finally:
                await temp_engine.dispose()

    def init_tenant_migrations(self, tenant_db_url: str) -> None:
        """
        Программный запуск Alembic для БД селлера.
        """
        try:
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", tenant_db_url)

            # Передаем параметр -x db_type=tenant, чтобы env.py отфильтровал только таблицы селлера
            alembic_cfg.cmd_opts = type("CmdOpts", (), {"x": ["db_type=tenant"]})()  # type: ignore[attr-defined]

            command.upgrade(alembic_cfg, "head")
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
        username = payload.get("sub")
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
    """Открывает сессий к центральной БД (для регистрации и логина)."""
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


T = TypeVar("T")


class TenantSessionManagerInterface(Protocol):
    async def get_session(self, db_url: str) -> AsyncIterator[AsyncSession]: ...
    async def get_repository(
        self, db_url: str, repo_cls: Type[T]
    ) -> AsyncIterator[T]: ...


class TenantSessionManager:
    """Отвечает за управление динамическими соединениями к БД тенентов."""

    @asynccontextmanager
    async def get_session(self, db_url: str) -> AsyncIterator[AsyncSession]:
        session_maker = get_sessionmaker(db_url)
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def get_repository(self, db_url: str, repo_cls: Type[T]) -> AsyncIterator[T]:
        """Утилитарный метод: создает сессию и сразу оборачивает ее в нужный репозиторий."""
        async with self.get_session(db_url) as session:
            yield repo_cls(session)  # pyright: ignore[reportCallIssue]
