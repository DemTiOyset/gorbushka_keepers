import asyncio

from app.auth.exceptions import (
    FailedInitialiseDatabaseError,
    UserAlreadyExistError,
    UserNotFoundError,
    UserUnauthorizedError,
)
from app.auth.repo import AuthRepositoryInterface
from app.auth.schemas import (
    CreateUserSchema,
    LoginUserSchema,
    RegisterUserSchema,
)
from app.auth.utils import create_access_token, hash_password, verify_password
from app.infrastructure.config import settings
from app.infrastructure.database import ProvisionerInterface
from app.infrastructure.models.user import User


class AuthHandler:
    def __init__(
        self, repo: AuthRepositoryInterface, provisioner: ProvisionerInterface
    ):
        self.repo = repo
        self.provisioner = provisioner

    async def handle_login_user(self, payload: LoginUserSchema):
        user_from_db: User | None = await self.repo.get_user_by_username_or_none(
            payload.username
        )

        if user_from_db is None:
            raise UserNotFoundError()

        is_password_valid = verify_password(
            plain_password=payload.password,
            hashed_password=user_from_db.hashed_password,
        )

        if not is_password_valid:
            raise UserUnauthorizedError()

        token_data = {"sub": user_from_db.username}

        access_token = create_access_token(data=token_data)

        return {"access_token": access_token, "token_type": "bearer"}

    async def handle_register_user(self, payload: RegisterUserSchema):
        user_from_db: User | None = await self.repo.get_user_by_username_or_none(
            payload.username
        )

        if user_from_db:
            raise UserAlreadyExistError()

        hashed_password = hash_password(payload.password)

        safe_db_name = f"db_{payload.username.lower().strip()}"
        tenant_url = settings.tenant_url(safe_db_name)

        try:
            # 3. ШАГ А: Физически создаем пустую базу на сервере PostgreSQL
            await self.provisioner.create_tenant_database(db_name=safe_db_name)

            # 4. ШАГ Б: Накатываем таблицы кассы внутрь только что созданной базы через Alembic
            # Запускаем в отдельном потоке, чтобы синхронный Alembic не блокировал асинхронный цикл FastAPI
            await asyncio.to_thread(self.provisioner.init_tenant_migrations, tenant_url)

        except Exception as e:
            raise FailedInitialiseDatabaseError(detail=str(e))

        new_user = CreateUserSchema(
            username=payload.username,
            hashed_password=hashed_password,
            database_url=tenant_url,
        )

        await self.repo.create_user(new_user.model_dump())
        await self.repo.commit()

        return {"status": "success", "detail": "Пользователь и его база данных созданы"}

    async def handle_delete_user(self, username: str):
        user_from_db: User | None = await self.repo.get_user_by_username_or_none(
            username
        )

        if user_from_db is None:
            raise UserNotFoundError()

        await self.repo.delete_user(user_from_db)
