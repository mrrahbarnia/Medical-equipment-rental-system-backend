import os
import sqlalchemy as sa
import sqlalchemy.orm as so

from uuid import uuid4
from typing import BinaryIO
from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from src.config import settings
from src.database import get_redis_connection
from src.pagination import paginate
from src.advertisement import exceptions
from src.advertisement import schemas
from src.advertisement import types
from src.advertisement.config import advertisement_settings
from src.s3.utils import upload_to_s3, delete_from_s3
from src.advertisement.models import Advertisement, Category, AdvertisementImage, Calendar
from src.auth.models import User

async def add_advertisement(
        session: async_sessionmaker[AsyncSession], user: User,
        payload: schemas.AdvertisementIn,
        video: UploadFile | None,
        images: list[UploadFile]
) -> None:
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
        engine: AsyncEngine, limit: int, offset: int, text__icontains: str | None,
        place__icontains: str | None, hour_price__range: str | None,
        day_price__range: str | None, week_price__range: str | None,
        month_price__range: str | None, category_name: str | None
):
    subquery = sa.select(AdvertisementImage).distinct(AdvertisementImage.advertisement_id).subquery()
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.description, Advertisement.place,
        Advertisement.hour_price, Advertisement.day_price, Advertisement.week_price,
        Advertisement.month_price, Category.id, Category.name.label("category_name"), subquery.c.url.label("image")
    ).select_from(Advertisement).join(
        subquery, Advertisement.id==subquery.c.advertisement_id, isouter=True
    ).join(
        Category, Advertisement.category_id==Category.id
    ).join(
        User, Advertisement.user_id==User.id
    ).where(sa.and_(
        Advertisement.published == True, Advertisement.is_deleted == False, User.is_banned == False # noqa
    )).order_by(Advertisement.created_at.desc())
    if text__icontains:
        query = query.where(sa.or_(
            Advertisement.title.ilike(f"%{text__icontains}%"),
            Advertisement.description.ilike(f"%{text__icontains}%")
        ))
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
    if category_name:
        parent_category_table_name = so.aliased(Category)
        category_subquery = (
            sa.select(Category.id)
            .select_from(Category)
            .join(
                parent_category_table_name,
                Category.parent_category==parent_category_table_name.id,
                isouter=True
            )
            .where(sa.or_(Category.name==category_name, parent_category_table_name.name==category_name))
        ).subquery()
        query = query.where(Category.id.in_(sa.select(category_subquery)))

    return await paginate(engine=engine, query=query, limit=limit, offset=offset)


async def list_my_advertisement(
        session: async_sessionmaker[AsyncSession],
        user: User
):
    subquery = sa.select(AdvertisementImage.url, AdvertisementImage.advertisement_id).distinct(
        AdvertisementImage.advertisement_id
    ).subquery()
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.admin_comment, Advertisement.views, Advertisement.published, subquery.c.url.label("image")
    ).select_from(Advertisement).join(
        subquery, Advertisement.id == subquery.c.advertisement_id
    ).where(Advertisement.user_id == user.id, Advertisement.is_deleted == False).order_by(Advertisement.created_at.desc()) # noqa
    async with session.begin() as conn:
        result = list((await conn.execute(query)).all())
    return result


async def delete_my_advertisement(
        session: async_sessionmaker[AsyncSession],
        user: User, advertisement_id: types.AdvertisementId
) -> None:
    owner_query = sa.select(Advertisement.id).where(sa.and_(
            Advertisement.user_id==user.id, Advertisement.id==advertisement_id, 
            Advertisement.is_deleted==False # noqa
        )
    )
    query = sa.update(Advertisement).where(Advertisement.id==advertisement_id).values(
        {
            Advertisement.is_deleted: True
        }
    )
    async with session.begin() as conn:
        result: types.AdvertisementId | None = await conn.scalar(owner_query)
        if result is None:
            raise exceptions.NotOwner
        await conn.execute(query)


async def get_advertisement(
        session: async_sessionmaker[AsyncSession],
        advertisement_id: types.AdvertisementId
):
    update_views_query = sa.update(Advertisement).where(Advertisement.id==advertisement_id).values(
        {
            Advertisement.views: Advertisement.views + 1
        }
    )
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.description, Advertisement.video,
        Advertisement.place, Advertisement.hour_price, Advertisement.day_price,
        Advertisement.week_price, Advertisement.month_price, AdvertisementImage.url,
        User.phone_number, Calendar.day, Category.name.label("category_name")
    ).select_from(Advertisement).join(
        AdvertisementImage, Advertisement.id==AdvertisementImage.advertisement_id
    ).join(Calendar, Advertisement.id==Calendar.advertisement_id).join(
        Category, Advertisement.category_id==Category.id
    ).where(
        sa.and_(
            Advertisement.id==advertisement_id,
            Advertisement.published==True, Advertisement.is_deleted==False # noqa
        )
    )
    async with session.begin() as conn:
        result = (await conn.execute(query)).all()
        if not result:
            raise exceptions.AdvertisementNotFound
        await conn.execute(update_views_query)
    return {
        "id": result[0].id, "title": result[0].title, "description": result[0].description, "video": result[0].video,
        "place": result[0].place, "hour_price": result[0].hour_price, "day_price": result[0].day_price,
        "week_price": result[0].week_price, "month_price": result[0].month_price,
        "image_urls": set([image.url for image in result]),
        "days": set([d.day for d in result]),
        "category_name": result[0].category_name
    }


async def show_phone_number(
        session: async_sessionmaker[AsyncSession], user: User, advertisement_id: types.AdvertisementId
):
    redis = get_redis_connection()
    r = redis.mget(keys=[f"{user.id}:hourly_rate", f"{user.id}:daily_rate"])
    if r[1] and int(r[1]) >= settings.REQUEST_PER_DAY: # type: ignore
        raise exceptions.DailyRateLimit
    if r[0] and int(r[0]) >= settings.REQUEST_PER_HOUR: # type: ignore
        raise exceptions.HourlyRateLimit 
    with redis.pipeline() as pipe:
        pipe.multi()
        if not r[0]: # type: ignore
            pipe.set(
                name=f"{user.id}:hourly_rate",
                value="1" if not r[0] else str(int(r[0]) + 1), # type: ignore
                ex=3600
            )
        else:
            pipe.incr(name=f"{user.id}:hourly_rate")
        if not r[1]: # type: ignore
            pipe.set(
                name=f"{user.id}:daily_rate",
                value="1" if not r[1] else str(int(r[1]) + 1), # type: ignore
                ex=86400
            )
        else:
            pipe.incr(name=f"{user.id}:daily_rate")
        pipe.execute()

    query = sa.select(User.phone_number).select_from(User).join(
        Advertisement, User.id==Advertisement.user_id
    ).where(Advertisement.id==advertisement_id)

    async with session.begin() as conn:
        phone_number = await conn.scalar(query)
    return phone_number


async def get_my_advertisement(
        session: async_sessionmaker[AsyncSession],
        user: User, advertisement_id: types.AdvertisementId
) -> dict:
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.description, Advertisement.video,
        Advertisement.place, Advertisement.hour_price, Advertisement.day_price,
        Advertisement.week_price, Advertisement.month_price, AdvertisementImage.url,
        User.phone_number, Calendar.day, Category.name.label("category_name")
    ).select_from(Advertisement).join(
        AdvertisementImage, Advertisement.id==AdvertisementImage.advertisement_id
    ).join(Calendar, Advertisement.id==Calendar.advertisement_id).join(
        Category, Advertisement.category_id==Category.id
    ).where(
        sa.and_(
            Advertisement.id==advertisement_id, Advertisement.user_id==user.id,
            Advertisement.is_deleted==False, Advertisement.admin_comment!=None # noqa
        )
    )
    async with session.begin() as conn:
        result = (await conn.execute(query)).all()
        if not result:
            raise exceptions.AdvertisementNotOwner
    return {
        "id": result[0].id, "title": result[0].title, "description": result[0].description, "video": result[0].video,
        "place": result[0].place, "hour_price": result[0].hour_price, "day_price": result[0].day_price,
        "week_price": result[0].week_price, "month_price": result[0].month_price,
        "image_urls": set([image.url for image in result]),
        "days": set([d.day for d in result]),
        "category_name": result[0].category_name
    }


async def update_my_advertisement(
        session: async_sessionmaker[AsyncSession],
        user: User,
        advertisement_id: types.AdvertisementId,
        payload: schemas.AdvertisementUpdate,
        video: UploadFile | None,
        images: list[UploadFile]
) -> None:
    owner_query = sa.select(Advertisement.id).where(sa.and_(
            Advertisement.user_id==user.id, Advertisement.id==advertisement_id,
            Advertisement.is_deleted==False, sa.and_( # noqa
                Advertisement.admin_comment.is_not(None),
                Advertisement.admin_comment!=""
            )
        )
    )
    async with session.begin() as conn:
        owner_result: types.AdvertisementId | None = await conn.scalar(owner_query)
    if owner_result is None:
        raise exceptions.UpdateMyAdException

    if video:
        assert video.filename is not None
        video_ext = os.path.splitext(video.filename)[1]
        unique_video_filename = f"{uuid4()}{video_ext}"
        if video.content_type not in (advertisement_settings.ADVERTISEMENT_VIDE_FORMATS.split(",")):
            raise exceptions.InvalidVideoFormat
        if video.size and video.size > advertisement_settings.ADVERTISEMENT_VIDEO_SIZE:
            raise exceptions.LargeVideoFile
        if payload.previous_video:
            await delete_from_s3((payload.previous_video.split("/")[-1])[:-1])

    if len(images) + len(payload.previous_images) > advertisement_settings.ADVERTISEMENT_IMAGES_LIMIT:
        raise exceptions.AdvertisementImageLimit

    if (len(images) + len(payload.previous_images)) == 1 and payload.previous_images[0] == "":
        raise exceptions.AtLeastOneImageExc

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

    if video:
        new_video_file_name = unique_video_filename
    elif not video and payload.previous_video:
        new_video_file_name = (payload.previous_video.split("/")[-1])[:-1]

    # Deleting all of the images
    delete_image_query = sa.delete(AdvertisementImage).where(
        AdvertisementImage.advertisement_id==advertisement_id
    )

    # Deleting all days
    delete_calendar_query = sa.delete(Calendar).where(
        Calendar.advertisement_id==advertisement_id
    )

    # Inserting new days
    calendar_query = sa.insert(Calendar).values(
        [
            {
                Calendar.day: selected_day,
                Calendar.advertisement_id: advertisement_id
            } for selected_day in payload.days
        ]
    )

    async with session.begin() as conn:
        # Check whether the provided category exists or not
        category_id: types.CategoryId | None = await conn.scalar(category_query)
        if not category_id:
            raise exceptions.InvalidCategoryName

        await conn.execute(delete_image_query)

        # Updating advertisement with new attributes
        advertisement_update_query = sa.update(Advertisement).where(Advertisement.id==advertisement_id).values(
            {
                Advertisement.title: payload.title,
                Advertisement.description: payload.description,
                Advertisement.place: payload.place,
                Advertisement.video: new_video_file_name if new_video_file_name else None,
                Advertisement.hour_price: payload.hour_price if payload.hour_price else None,
                Advertisement.day_price: payload.day_price if payload.day_price else None,
                Advertisement.week_price: payload.week_price if payload.week_price else None,
                Advertisement.month_price: payload.month_price if payload.month_price else None,
                Advertisement.category_id: category_id,
                Advertisement.admin_comment: None
            }
        )

        await conn.execute(delete_calendar_query)

        try:
            await conn.execute(calendar_query)
        except IntegrityError:
            raise exceptions.DuplicateSelectedDays

        await conn.execute(advertisement_update_query)
        if len(images) > 0:
            image_query = sa.insert(AdvertisementImage).values(
                [
                    {
                        AdvertisementImage.url: image_name,
                        AdvertisementImage.advertisement_id: advertisement_id
                    } for image_name in image_unique_names
                ]
            )
            await conn.execute(image_query)

        if len(payload.previous_images) > 0 and payload.previous_images[0] != "":
            previous_image_query = sa.insert(AdvertisementImage).values(
                [
                    {
                        AdvertisementImage.url: ((image_name.split("/"))[-1])[:-1],
                        AdvertisementImage.advertisement_id: advertisement_id
                    } for image_name in payload.previous_images
                ]
            )
            await conn.execute(previous_image_query)

    # Uploading images
    if video:
        await upload_to_s3(file=video.file, unique_filename=unique_video_filename)

    for image_unique_name, image_file in image_unique_names.items():
        await upload_to_s3(file=image_file, unique_filename=image_unique_name)
