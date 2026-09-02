# ============================================================================
# DOZOR — Makefile (GNU Make)
# ============================================================================
# Все команды запускаются из корня проекта (там где docker-compose.yml).
#
# ДВА ОСНОВНЫХ РЕЖИМА:
#
#   1. ЛОКАЛЬНО БЕЗ CADDY (одна команда, Vite dev server + hot-reload):
#      make up                  — поднять весь стек в Docker (БД + бекенд + Vite)
#      make down                — остановить
#      make rebuild             — пересобрать и перезапустить (локально)
#      make rebuild-frontend    — пересобрать только фронтенд
#      Фронтенд: http://localhost:5173   Бекенд: http://localhost:8000
#
#   2. ПРОДАКШЕН (Caddy + Let's Encrypt):
#      make prod                — поднять стек с HTTPS (https://app-dozor.ru)
#      make prod-down           — остановить
#      make build-prod          — собрать продакшен-образы
#
#   (опционально) ХОСТОВАЯ РАЗРАБОТКА без Docker для фронта/бека:
#      make dev-db              — только PostgreSQL в Docker
#      make dev-backend         — бекенд на хосте (uvicorn --reload)
#      make dev-frontend        — фронтенд на хосте (npm run dev)
#      make dev-create-user / dev-bind-store / dev-seed
#
#   CLI / ТЕСТЫ (работают когда поднят Docker-стек):
#      make create-user         — создать пользователя (через Docker)
#      make bind-store          — привязать магазин (через Docker)
#      make seed                — заполнить заказами (через Docker)
#      make test                — прогнать автотест (через Docker)
#
#   ЛОГИ:
#      make logs                — все логи (Docker)
#      make logs-backend        — бекенд (Docker)
#      make logs-frontend       — фронтенд (Docker)
# ============================================================================

.PHONY: dev dev-db dev-backend dev-frontend dev-create-user dev-bind-store dev-seed \
        up prod down prod-down build build-prod \
        test seed create-user bind-store cli \
        logs logs-backend logs-frontend \
        rebuild rebuild-frontend

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  1. ЛОКАЛЬНАЯ РАЗРАБОТКА БЕЗ CADDY (hot-reload)                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# В этом режиме:
#   - PostgreSQL работает в Docker (localhost:5432)
#   - Бекенд запускается через `uv run uvicorn` с --reload
#   - Фронтенд запускается через `npm run dev` (Vite dev server с HMR)
#   - Vite проксирует /api/* → http://localhost:8000 (без префикса /api)
#
# ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ:
#   - Docker (для postgres)
#   - Python 3.13+ с uv (pip install uv)
#   - Node.js 20+ (для фронтенда)

# Запустить ТОЛЬКО PostgreSQL — база нужна и бекенду, и CLI
dev-db:
	docker compose up -d postgres
	@echo ""
	@echo "✅ PostgreSQL на localhost:5432 (юзер: osman, пароль: osman)"

# Бекенд: uvicorn с авто-перезагрузкой при изменении .py файлов
dev-backend:
	@echo "🚀 Бекенд: http://localhost:8000 (Ctrl+C чтобы остановить)"
	@echo "   Swagger: http://localhost:8000/docs"
	@echo ""
	DATABASE_URL=postgresql+asyncpg://osman:osman@localhost:5432/system_meta \
	POSTGRES_HOST=localhost \
	POSTGRES_PORT=5432 \
	POSTGRES_USER=osman \
	POSTGRES_PASSWORD=osman \
	SECRET_KEY=9ZC+2mYiBzR+MX6Vjq7f8SM4idTGft2DRz+CJ/zNKnE= \
	ALGORITHM=HS256 \
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Фронтенд: Vite dev server с hot module replacement
# Запускать в ОТДЕЛЬНОМ терминале после dev-backend
dev-frontend:
	@echo "🚀 Фронтенд: http://localhost:5173 (Ctrl+C чтобы остановить)"
	@echo ""
	cd frontend && npm install && npm run dev

# CLI команды для локального режима (подключаются к localhost:5432)
dev-create-user:
	DATABASE_URL=postgresql+asyncpg://osman:osman@localhost:5432/system_meta \
	uv run python -m app.auth.cli

dev-bind-store:
	DATABASE_URL=postgresql+asyncpg://osman:osman@localhost:5432/system_meta \
	uv run python -m app.users.cli

dev-seed:
	DATABASE_URL=postgresql+asyncpg://osman:osman@localhost:5432/system_meta \
	uv run python -m app.orders.seed test_user

# Запустить БД и показать инструкцию для запуска бекенда и фронтенда
dev: dev-db
	@echo "📋 Дальше — в двух отдельных терминалах:"
	@echo "   Терминал 1: make dev-backend"
	@echo "   Терминал 2: make dev-frontend"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  2. DOCKER: ЛОКАЛЬНО (без Caddy) И ПРОДАКШЕН (Caddy)                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Локальный запуск (`make up`) использует docker-compose.override.yml, который
# заменяет Caddy-фронтенд на Vite dev server. Compose мёржит override-файл
# автоматически при `docker compose up` БЕЗ -f.
#
# Прод (`make prod`) использует ТОЛЬКО docker-compose.yml (флаг -f), поэтому
# override-файл игнорируется и работает оригинальный Caddy + Let's Encrypt.

# Локально: весь стек одной командой, БЕЗ Caddy (Vite на 5173).
up:
	docker compose up -d
	@echo ""
	@echo "✅ Фронтенд (Vite, без Caddy): http://localhost:5173"
	@echo "✅ Бекенд:                    http://localhost:8000"
	@echo "✅ База:                      localhost:5432"
	@echo ""
	@echo "Дальше: make create-user → make bind-store → make seed"

# Продакшен: только базовый docker-compose.yml (Caddy + HTTPS).
# Перед запуском убедись:
#   1. DNS указывает на этот сервер (app-dozor.ru → твой IP)
#   2. Порты 80 и 443 свободны (останови nginx/apache если есть)
prod:
	docker compose -f docker-compose.yml up -d
	@echo ""
	@echo "⏳ Caddy получает HTTPS-сертификат (10-30 сек)..."
	@echo "   Проверить:  make logs-frontend"
	@echo ""
	@echo "После получения сертификата:"
	@echo "   ✅ https://app-dozor.ru"
	@echo "   make create-user → make bind-store → make seed"

down:
	docker compose down

prod-down:
	docker compose -f docker-compose.yml down

# Собрать образы для локального режима (Vite)
build:
	docker compose build

# Собрать образы для продакшена (Caddy)
build-prod:
	docker compose -f docker-compose.yml build


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  3. CLI И ТЕСТЫ (Docker)                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Эти команды используют docker compose exec backend и работают когда поднят
# Docker-стек (make up или make prod).
# Для хостового режима используй dev-create-user / dev-bind-store / dev-seed.

test:
	docker compose exec backend uv run pytest tests/test_add_order_created.py -v -s

seed:
	docker compose exec backend uv run python -m app.orders.seed test_user

create-user:
	docker compose exec backend uv run python -m app.auth.cli

bind-store:
	docker compose exec backend uv run python -m app.users.cli

# Полный цикл (только Docker-режим)
cli: create-user bind-store seed


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  4. ЛОГИ (Docker)                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

logs:
	docker compose logs -f

logs-backend:
	docker compose logs backend -f

logs-frontend:
	docker compose logs frontend -f


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  5. ПЕРЕСБОРКА (локально, через override)                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Эти команды собирают ЛОКАЛЬНЫЙ образ (Vite). Для продакшена используй
# `make build-prod`, затем `make prod`.

rebuild:
	docker compose build
	docker compose up -d

rebuild-frontend:
	docker compose build frontend
	docker compose up -d frontend
