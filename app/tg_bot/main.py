# app/tg_bot/bot.py

import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.infrastructure.config import settings
from app.tg_bot.handlers import (
    callback_query_handler,
    show_pending_returns_message,
    start_command,
)

logger = logging.getLogger(__name__)


def create_bot_application() -> Application:
    token = settings.TG_BOT_TOKEN

    if not token:
        raise RuntimeError("TG_BOT_TOKEN не задан")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("pending", show_pending_returns_message))

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & (
                filters.Regex("(?i)непришедш")
                | filters.Regex("(?i)возврат")
                | filters.Regex("(?i)обновить")
            ),
            show_pending_returns_message,
        )
    )

    app.add_handler(CallbackQueryHandler(callback_query_handler))

    return app


async def bot_main():
    """Точка входа для запуска бота в режиме polling."""
    token = settings.TG_BOT_TOKEN
    if not token:
        print("Ошибка: Переменная окружения TG_BOT_TOKEN не задана.")
        print("Укажите валидный токен бота в .env файле.")
        sys.exit(1)

    print("🚀 Запуск Telegram-бота Дозор · Возвраты...")
    app = await create_bot_application()
    app.run_polling()


# if __name__ == "__main__":
#     asyncio.run(main())
