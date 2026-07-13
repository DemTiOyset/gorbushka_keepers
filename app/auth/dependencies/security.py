from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.infrastructure.config import (
    settings,
)


def hash_password(password: str) -> str:
    """
    Принимает чистый пароль, генерирует соль
    и возвращает безопасный хэш для сохранения в БД.
    """
    # Переводим пароль в байты
    password_bytes = password.encode("utf-8")

    # Генерируем соль (rounds=12 — оптимальный баланс скорости и защиты)
    salt = bcrypt.gensalt(rounds=12)

    # Хэшируем
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)

    # Возвращаем строкой для записи в varchar/string поле БД
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнивает чистый пароль от пользователя с хэшем из базы данных.
    Возвращает True, если они совпадают.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    # Функция сама извлечет соль из хэша и сравнит их защищенным от тайминг-атак методом
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Генерирует зашифрованный JWT токен.
    """
    to_encode = data.copy()

    # Задаем время жизни токена (например, 1 день, если не передано иное)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=1)

    # exp — стандартный заголовок JWT (expiration time)
    to_encode.update({"exp": expire})

    # Кодируем данные с помощью секретного ключа приложения
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
