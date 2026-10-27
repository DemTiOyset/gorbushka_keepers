"""
Это модуль авторизации,
пусть изначально при входе на страничку пользователя встречает страничка входа,
если аккаунта нет, пусть внизу будет кнопочка зарегистрироваться.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_provisioner_obj, get_repo_obj
from app.auth.exceptions import UserNotFoundError, UserUnauthorizedError
from app.auth.schemas import LoginUserSchema
from app.auth.services import AuthHandler

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_user(
    payload: LoginUserSchema,
    repo=Depends(get_repo_obj),
    provisioner=Depends(get_provisioner_obj),
):
    """
    Это роутер входа, после входа пользователю выдается токен, который фронт должен вшить и передавать при каждом запросе в другие модули.
    """
    try:
        handler = AuthHandler(repo=repo, provisioner=provisioner)
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
