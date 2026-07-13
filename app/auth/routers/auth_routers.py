from fastapi import APIRouter, Depends

from app.auth.schemas.user_schemas import LoginUserSchema, RegisterUserSchema
from app.auth.services.handle_auth import AuthHandler

from ..repositories.dependencies import get_repo_obj

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_user(payload: LoginUserSchema, repo=Depends(get_repo_obj)):
    handler = AuthHandler(repo=repo)
    return await handler.handle_login_user(payload=payload)


@router.post("/register")
async def register_user(payload: RegisterUserSchema, repo=Depends(get_repo_obj)):
    handler = AuthHandler(repo=repo)
    return await handler.handle_register_user(payload=payload)
