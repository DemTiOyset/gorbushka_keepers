import asyncio

from fastapi import HTTPException, status

from app.auth.schemas.user_schemas import LoginUserSchema, RegisterUserSchema
from app.infrastructure.database import create_tenant_database, init_tenant_migrations
from app.infrastructure.models.user import User

from ..dependencies.security import create_access_token, hash_password, verify_password
from ..repositories.auth_repo import AuthRepository


class AuthHandler:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def handle_login_user(self, payload: LoginUserSchema):
        user_from_db: User | None = await self.repo.get_user_by_username_or_none(
            payload.username
        )

        if user_from_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Данный пользователь не зарегистрирован.",
            )

        is_password_valid = verify_password(
            plain_password=payload.password,
            hashed_password=user_from_db.hashed_password,
        )

        if not is_password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль.",
            )

        token_data = {"sub": user_from_db.username}

        access_token = create_access_token(data=token_data)

        return {"access_token": access_token, "token_type": "bearer"}

    async def handle_register_user(self, payload: RegisterUserSchema):
        user_from_db: User | None = await self.repo.get_user_by_username_or_none(
            payload.username
        )

        if user_from_db:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Данный уже существует.",
            )

        hashed_password = hash_password(payload.password)

        safe_db_name = f"db_{payload.username.lower().strip()}"
        tenant_url = f"postgresql+asyncpg://osman:osman@localhost:5432/{safe_db_name}"

        try:
            # 3. ШАГ А: Физически создаем пустую базу на сервере PostgreSQL
            await create_tenant_database(db_name=safe_db_name)

            # 4. ШАГ Б: Накатываем таблицы кассы внутрь только что созданной базы через Alembic
            # Запускаем в отдельном потоке, чтобы синхронный Alembic не блокировал асинхронный цикл FastAPI
            await asyncio.to_thread(init_tenant_migrations, tenant_url)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось инициализировать персональную базу данных: {str(e)}",
            )

        new_user = User(
            username=payload.username,
            hashed_password=hashed_password,
            database_url=tenant_url,
        )

        self.repo.session.add(new_user)
        await self.repo.session.commit()

        return {"status": "success", "detail": "Пользователь и его база данных созданы"}
