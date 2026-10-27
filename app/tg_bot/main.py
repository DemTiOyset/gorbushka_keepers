import asyncio
import logging
import sys

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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_bot_application() -> Application:
    """Создает и настраивает приложение Telegram-бота."""
    token = settings.TG_BOT_TOKEN
    if not token:
        logger.error(
            "TG_BOT_TOKEN не задан! Пожалуйста, укажите токен в .env или в окружении."
        )

    builder = ApplicationBuilder().token(token or "DUMMY_TOKEN")
    app = builder.build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("pending", show_pending_returns_message))

    # Регистрация текстовых сообщений из меню
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

    # Регистрация обработки всех инлайн-кнопок
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    return app


def main():
    """Точка входа для запуска бота в режиме polling."""
    token = settings.TG_BOT_TOKEN
    if not token:
        print("Ошибка: Переменная окружения TG_BOT_TOKEN не задана.")
        print("Укажите валидный токен бота в .env файле.")
        sys.exit(1)

    print("🚀 Запуск Telegram-бота Дозор · Возвраты...")
    app = create_bot_application()
    app.run_polling()


if __name__ == "__main__":
    main()
