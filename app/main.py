import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit.routers import router as audit_router
from app.auth.routers import router as auth_router
from app.orders.routers import router as order_router
from app.tg_bot.main import create_bot_application
from app.users.routers import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    telegram_app = create_bot_application()

    try:
        # 1. Инициализируем Telegram Application.
        await telegram_app.initialize()

        # 2. Запускаем обработчик очереди обновлений.
        await telegram_app.start()

        # 3. Запускаем получение обновлений от Telegram.
        await telegram_app.updater.start_polling()  # pyright: ignore[reportOptionalMemberAccess]

        app.state.telegram_app = telegram_app

        logger.info("Telegram bot started")

        yield

    finally:
        # 4. Останавливаем получение обновлений.
        if telegram_app.updater.running:  # pyright: ignore[reportOptionalMemberAccess]
            await telegram_app.updater.stop()  # pyright: ignore[reportOptionalMemberAccess]

        # 5. Останавливаем Application.
        if telegram_app.running:
            await telegram_app.stop()

        # 6. Освобождаем ресурсы Telegram.
        await telegram_app.shutdown()

        logger.info("Telegram bot stopped")


app = FastAPI(lifespan=lifespan)
app: FastAPI = FastAPI(
    title="Gorbushka Keepers Ozon", version="1.0.0", lifespan=lifespan
)

app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(order_router)


# Список разрешенных источников (origins)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:80",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # разрешить запросы с этих адресов
    allow_credentials=True,  # разрешить передачу кук/авторизационных заголовков
    allow_methods=["*"],  # разрешить все методы (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # разрешить все заголовки
)


@app.get("/health")
async def health():
    return {"status": "ok"}
