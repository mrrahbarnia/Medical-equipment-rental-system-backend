import os
import sqlalchemy as sa

from uuid import uuid4
from typing import BinaryIO
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from src.pagination import paginate
from src.advertisement import exceptions
from src.advertisement import schemas
from src.advertisement import types
from src.advertisement.config import advertisement_settings
from src.s3.utils import upload_to_s3
from src.advertisement.models import Advertisement, Category, AdvertisementImage, Calendar
from src.auth.models import User

async def add_advertisement(
        session: async_sessionmaker[AsyncSession], user: User,
        payload: schemas.AdvertisementIn,
        video: UploadFile | None,
        images: list[UploadFile]
):
    # Validating video
    if video:
        assert video.filename is not None
        video_ext = os.path.splitext(video.filename)[1]
        unique_video_filename = f"{uuid4()}{video_ext}"
        if video.content_type not in (advertisement_settings.ADVERTISEMENT_VIDE_FORMATS.split(",")):
            raise exceptions.InvalidVideoFormat
        if video.size and video.size > advertisement_settings.ADVERTISEMENT_VIDEO_SIZE:
            raise exceptions.LargeVideoFile

    # Validating images
    if len(images) > advertisement_settings.ADVERTISEMENT_IMAGES_LIMIT:
        raise exceptions.AdvertisementImageLimit
    image_unique_names: dict[str, BinaryIO] = dict()
    for image in images:
        if image.size and image.size > advertisement_settings.ADVERTISEMENT_IMAGE_SIZE:
            raise exceptions.LargeImageFile
        if image.content_type not in (advertisement_settings.ADVERTISEMENT_IMAGE_FORMATS.split(",")):
            raise exceptions.InvalidImageFormat
        assert image.filename is not None
        image_ext = os.path.splitext(image.filename)[1]
        unique_image_filename = f"{uuid4()}{image_ext}"
        image_unique_names[unique_image_filename] = image.file

    category_query = sa.select(Category.id).where(Category.name==payload.category_name)
    user_query = sa.update(User).where(User.id==user.id).values(
        {
            User.has_subscription_fee: False
        }
    )
    async with session.begin() as conn:
        category_id: types.CategoryId | None = await conn.scalar(category_query)
        if not category_id:
            raise exceptions.InvalidCategoryName
        advertisement_query = sa.insert(Advertisement).values(
                {
                    Advertisement.title: payload.title,
                    Advertisement.description: payload.description,
                    Advertisement.place: payload.place,
                    Advertisement.video: unique_video_filename if video else None,
                    Advertisement.hour_price: payload.hour_price if payload.hour_price else None,
                    Advertisement.day_price: payload.day_price if payload.day_price else None,
                    Advertisement.week_price: payload.week_price if payload.week_price else None,
                    Advertisement.month_price: payload.month_price if payload.month_price else None,
                    Advertisement.category_id: category_id,
                    Advertisement.user_id: user.id
                }
            ).returning(Advertisement.id)
        advertisement_id: types.AdvertisementId | None = await conn.scalar(advertisement_query)
        await conn.execute(user_query)
        image_query = sa.insert(AdvertisementImage).values(
                [
                    {
                        AdvertisementImage.url: image_name,
                        AdvertisementImage.advertisement_id: advertisement_id
                    } for image_name in image_unique_names
                ]
            )
        calendar_query = sa.insert(Calendar).values(
            [
                {
                    Calendar.day: selected_day,
                    Calendar.advertisement_id: advertisement_id
                } for selected_day in payload.days
            ]
        )
        await conn.execute(image_query)
        try:
            await conn.execute(calendar_query)
        except IntegrityError:
            raise exceptions.DuplicateSelectedDays

    # Uploading video
    if video:
        await upload_to_s3(file=video.file, unique_filename=unique_video_filename)

    # Uploading images
    for image_unique_name, image_file in image_unique_names.items():
        await upload_to_s3(file=image_file, unique_filename=image_unique_name)


async def get_published_advertisement(
        engine: AsyncEngine, limit: int, offset: int, title__icontains: str | None,
        description__icontains: str | None, place__icontains: str | None,
        hour_price__range: str | None, day_price__range: str | None,
        week_price__range: str | None, month_price__range: str | None
):
    subquery = sa.select(AdvertisementImage).distinct(AdvertisementImage.advertisement_id).subquery()
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.description, Advertisement.place,
        Advertisement.hour_price, Advertisement.day_price, Advertisement.week_price,
        Advertisement.month_price, subquery.c.url.label("image")
    ).select_from(Advertisement).join(
        subquery, Advertisement.id==subquery.c.advertisement_id, isouter=True
    ).where(Advertisement.published == True) # noqa
    if title__icontains:
        query = query.where(Advertisement.title.ilike(f"%{title__icontains}%"))
    if description__icontains:
        query = query.where(Advertisement.description.ilike(f"%{description__icontains}%"))
    if place__icontains:
        query = query.where(Advertisement.place.ilike(f"%{place__icontains}%"))
    if hour_price__range:
        query = query.where(Advertisement.hour_price.between(
            float(hour_price__range.split(",")[0]), float(hour_price__range.split(",")[1])
        ))
    if day_price__range:
        query = query.where(Advertisement.day_price.between(
            float(day_price__range.split(",")[0]), float(day_price__range.split(",")[1])
        ))
    if week_price__range:
        query = query.where(Advertisement.week_price.between(
            float(week_price__range.split(",")[0]), float(week_price__range.split(",")[1])
        ))
    if month_price__range:
        query = query.where(Advertisement.month_price.between(
            float(month_price__range.split(",")[0]), float(month_price__range.split(",")[1])
        ))

    return await paginate(engine=engine, query=query, limit=limit, offset=offset)
