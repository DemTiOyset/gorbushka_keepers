# Бэкенд на FastAPI с uv в качестве dependency manager.
# Запускается через uvicorn. Multi-tenant базы данных (db_*) создаются
# в сервисе postgres из docker-compose.

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Устанавливаем системные зависимости для asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Сначала копируем только манифесты для кэширования зависимостей
COPY pyproject.toml uv.lock* ./

# Синхронизируем зависимости в виртуальное окружение
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Копируем остальной код
COPY . .

# Миграции системной БД и запуск приложения
EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
