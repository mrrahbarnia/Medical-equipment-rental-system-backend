from typing import Annotated, Optional, Union
from fastapi import APIRouter, status, Depends, UploadFile, Form, File
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.database import get_session
from src.advertisement import service
from src.advertisement.dependencies import check_subscription_fee
from src.advertisement import schemas
from src.auth.models import User

router = APIRouter()


@router.post(
    "/add-advertisement/",
    status_code=status.HTTP_201_CREATED,
    # response_model=schemas.AdvertisementOut
)
async def add_advertisement(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    place: Annotated[str, Form()],
    category_name: Annotated[str, Form(alias="categoryName", validation_alias="categoryName")],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(check_subscription_fee)],
    images: list[UploadFile],
    video: UploadFile | None = None,
):
    await service.add_advertisement(
        session=session, title=title, description=description,
        place=place, user=current_user, video_size=video.size if video else None,
        video_format=video.content_type if video else None,
        video_filename=video.filename if video else None,
        video_file=video.file if video else None,
        images=images,
        category_name=category_name
    )
    return {
        "title": title, "description": description, "place": place
    }
