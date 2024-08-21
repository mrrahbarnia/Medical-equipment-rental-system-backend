import os
import sqlalchemy as sa

from uuid import uuid4
from typing import BinaryIO
from fastapi import UploadFile
from aiobotocore.session import get_session # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.advertisement import exceptions
from src.advertisement import types
from src.advertisement.config import advertisement_settings
from src.advertisement.models import Advertisement, Category, AdvertisementImage
from src.auth.models import User

async def add_advertisement(
        session: async_sessionmaker[AsyncSession], title: str,
        description: str, place: str, user: User, video_size: int | None,
        video_format: str | None, video_filename: str | None, video_file: BinaryIO | None,
        category_name: str, images: list[UploadFile]
):
    if video_format and video_format not in (advertisement_settings.ADVERTISEMENT_VIDE_FORMATS.split(",")):
        raise exceptions.InvalidVideoFormat
    if video_size and video_size > advertisement_settings.ADVERTISEMENT_VIDEO_SIZE:
        raise exceptions.LargeVideoFile
    assert len(images) != 0
    image_unique_names = list()
    for image in images:
        assert image.size and image.content_type and image.filename is not None
        if image.size > advertisement_settings.ADVERTISEMENT_IMAGE_SIZE:
            raise exceptions.LargeImageFile
        if image.content_type not in (advertisement_settings.ADVERTISEMENT_IMAGE_FORMATS.split(",")):
            raise exceptions.InvalidImageFormat
        image_ext = os.path.splitext(image.filename)[1]
        image_unique_name = uuid4()
        new_image_filename = f"{image_unique_name}{image_ext}"
        image_unique_names.append(new_image_filename)
    if len(images) > advertisement_settings.ADVERTISEMENT_IMAGES_LIMIT:
        raise exceptions.AdvertisementImageLimit
    if video_filename:
        video_ext = os.path.splitext(video_filename)[1]
        video_unique_name = uuid4()
        new_video_filename = f"{video_unique_name}{video_ext}"
        boto_session = get_session()
        async with boto_session.create_client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        ) as client:
            await client.put_object(
                Bucket=settings.BUCKET_NAME,
                Key=new_video_filename,
                Body=video_file
            )
    category_query = sa.select(Category.id).where(Category.name==category_name)
    user_query = sa.update(User).where(User.id==user.id).values(
        {
            User.has_subscription_fee: False
        }
    )
    
    async with session.begin() as conn:
        category_id: types.CategoryId | None = await conn.scalar(category_query)
        if not category_id:
            raise exceptions.InvalidCategoryName
        query = sa.insert(Advertisement).values(
                {
                    Advertisement.title: title,
                    Advertisement.description: description,
                    Advertisement.place: place,
                    Advertisement.video: new_video_filename if video_filename else None,
                    Advertisement.category_id: category_id,
                    Advertisement.user_id: user.id
                }
            ).returning(Advertisement.id)
        await conn.execute(user_query)
        advertisement_id: types.AdvertisementId | None = await conn.scalar(query)
        # image_query = sa.insert(AdvertisementImage).values(
        #         [

        #         ]
        #     )

    # return new_video_filename if video_filename else None
