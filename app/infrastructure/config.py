from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Глобальные настройки приложения.

    Все значения можно переопределить через переменные окружения или .env файл.
    """

    # Основной URL базы данных (асинхронный postgres через asyncpg).
    # Используется глобальным engine-ом для миграций и фоновыми задачами
    # (scheduler). По умолчанию совпадает с БД seller_1.
    DATABASE_URL: str = "postgresql+asyncpg://osman:osman@localhost:5432/system_meta"

    # Учётные данные Ozon Seller API
    CLIENT_ID: str = ""
    API_KEY: str = ""

    # Telegram-бот для уведомлений о возвратах
    TG_BOT_TOKEN: str = ""
    TG_CHAT_ID: str = ""

    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "9ZC+2mYiBzR+MX6Vjq7f8SM4idTGft2DRz+CJ/zNKnE="

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )


settings = Settings()
