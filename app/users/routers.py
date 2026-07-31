from fastapi import APIRouter, Depends

from app.users.dependencies import get_repo_obj
from app.users.schemas import StoreDataDTO
from app.users.services import UserHandler

router = APIRouter(prefix="users", tags=["user"])


@router.post("/")
async def create_store(store_data: StoreDataDTO, repo=Depends(get_repo_obj)):
    handler = UserHandler(repo)
    return await handler.create_store(store_data)
