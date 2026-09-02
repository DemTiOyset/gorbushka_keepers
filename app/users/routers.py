from fastapi import APIRouter, Depends

from app.users.dependencies import get_user_repo_obj
from app.users.schemas import StoreDataSchema
from app.users.services import UserHandler

router = APIRouter(prefix="/users", tags=["user"])


@router.post("/")
async def create_store(store_data: StoreDataSchema, repo=Depends(get_user_repo_obj)):
    handler = UserHandler(repo)
    return await handler.create_store(store_data=store_data)
