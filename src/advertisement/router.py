from typing import Annotated
from fastapi import APIRouter, status, Depends, UploadFile, Form
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.database import get_session
from src.advertisement.dependencies import check_subscription_fee
from src.advertisement import schemas
from src.auth.models import User


router = APIRouter()


@router.post(
    "/add-advertisement/",
    status_code=status.HTTP_201_CREATED
)
async def add_advertisement(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    place: Annotated[str, Form()],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(check_subscription_fee)],
    video: UploadFile | None = None
):
    if video:
        print(video.size)
    return "OK"