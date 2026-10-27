import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.infrastructure.config import settings

# Импортируем ваш Base
from app.infrastructure.database import Base

# Явный импорт моделей, чтобы Alembic их гарантированно "увидел"
from app.infrastructure.models.audit_action import AuditAction
from app.infrastructure.models.cash import Cash
from app.infrastructure.models.user import User

config = context.config

# Переопределяем URL из настроек приложения, чтобы он подхватывал
# переменные окружения (важно для docker-compose). Если URL уже явно
# установлен программно (через set_main_option для tenant-базы) — он сохранится.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# ФУНКЦИЯ ФИЛЬТРАЦИИ ТАБЛИЦ (Умное разделение на Системную БД и БД Селлеров)
# ---------------------------------------------------------------------------
def include_object(object, name, type_, reflected, compare_to):
    """
    Определяет, какие таблицы включать в миграцию.
    Разделяет таблицы на Системную БД (users) и БД Селлеров (audit, cash).
    """
    # 1. Проверяем аргумент из консоли (-x db_type=system)
    x_args = context.get_x_argument(as_dictionary=True)
    db_type_x = x_args.get("db_type")

    # 2. Проверяем тег из программного вызова (tag="tenant")
    # context.get_tag_argument() возвращает строку или None
    tag = context.get_tag_argument()

    # Определяем итоговый режим работы
    if db_type_x == "system" or tag == "system":
        is_system = True
    elif db_type_x == "tenant" or tag == "tenant":
        is_system = False
    else:
        # Дефолтное поведение, если ничего не передано
        is_system = False

    # Фильтруем таблицы по их именам
    if is_system:
        # В системной базе должна быть ТОЛЬКО таблица users
        return name == "users"
    else:
        # В базах селлеров таблицы users быть НЕ ДОЛЖНО
        return name != "users"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,  # Подключаем фильтр
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Вспомогательная синхронная функция для выполнения миграций внутри транзакции."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,  # Подключаем фильтр
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (Переписано под Async и Multi-tenancy)."""

    # Используем async_engine_from_config вместо синхронного аналога
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Так как Alembic внутри синхронный, мы запускаем его через run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запускаем асинхронный цикл для online-режима
    asyncio.run(run_migrations_online())
