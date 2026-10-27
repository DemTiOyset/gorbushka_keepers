from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Глобальные настройки приложения.

    Все значения можно переопределить через переменные окружения или .env файл.
    """

    # Основной URL базы данных (асинхронный postgres через asyncpg).
    # Используется глобальным engine-ом для миграций и фоновыми задачами
    # (scheduler). По умолчанию совпадает с БД seller_1.
    DATABASE_URL: str = "postgresql+asyncpg://osman:osman@db:5432/system_meta"

    # Параметры подключения к PostgreSQL. Используются при динамическом
    # создании tenant-баз данных (POSTGRES_HOST обычно = имени сервиса в
    # docker-compose, например 'postgres').
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "osman"
    POSTGRES_PASSWORD: str = "osman"

    @property
    def postgres_dsn_base(self) -> str:
        """DSN без имени базы — для подключения к системной БД postgres."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
        )

    @property
    def postgres_admin_url(self) -> str:
        return f"{self.postgres_dsn_base}/postgres"

    def tenant_url(self, db_name: str) -> str:
        return f"{self.postgres_dsn_base}/{db_name}"

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
