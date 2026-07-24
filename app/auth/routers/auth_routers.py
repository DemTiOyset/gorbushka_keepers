"""
Это модуль авторизации,
пусть изначально при входе на страничку пользователя встречает страничка входа,
если аккаунта нет, пусть внизу будет кнопочка зарегистрироваться.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.schemas.user_exc import (
    FailedInitialiseDatabaseError,
    UserAlreadyExistError,
    UserNotFoundError,
    UserUnauthorizedError,
)
from app.auth.schemas.user_schemas import LoginUserSchema, RegisterUserSchema
from app.auth.services.handle_auth import AuthHandler

from ..repositories.dependencies import get_repo_obj

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_user(payload: LoginUserSchema, repo=Depends(get_repo_obj)):
    """
    Это роутер входа, после входа пользователю выдается токен, который фронт должен вшить и передавать при каждом запросе в другие модули.
    """
    try:
        handler = AuthHandler(repo=repo)
        return await handler.handle_login_user(payload=payload)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Данный пользователь не зарегистрирован.",
        )
    except UserUnauthorizedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль.",
        )
