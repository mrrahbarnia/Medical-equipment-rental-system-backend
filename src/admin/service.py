import sqlalchemy as sa
import sqlalchemy.orm as so

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from src.pagination import paginate
from src.admin import schemas
from src.admin import exceptions
from src.advertisement.types import CategoryId, AdvertisementId
from src.advertisement.models import Category, Advertisement, AdvertisementImage, Calendar
from src.advertisement.exceptions import AdvertisementNotFound
from src.auth.models import User
from src.auth.exceptions import UserNotFound
from src.auth.types import PhoneNumber, UserId
from src.s3.utils import delete_from_s3


async def add_category(
        session: async_sessionmaker[AsyncSession], payload: schemas.Category
) -> None:
    if payload.parent_category_name:
        parent_query = sa.select(Category).where(Category.name==payload.parent_category_name)
        async with session.begin() as conn:
            parent_category: Category | None = await conn.scalar(parent_query)
            if parent_category is None:
                raise exceptions.InvalidParentCategoryName
            query = sa.insert(Category).values(
                {
                    Category.name: payload.name,
                    Category.parent_category: parent_category.id
                }
            )
            try:
                async with session.begin() as conn:
                    await conn.scalars(query)
            except IntegrityError:
                raise exceptions.DuplicateCategoryName
    else:
        without_parent_query = sa.insert(Category).values(
            {
                Category.name: payload.name,
            }
        )
        try:
            async with session.begin() as conn:
                await conn.execute(without_parent_query)
        except IntegrityError:
            raise exceptions.DuplicateCategoryName
        


async def search_category_by_name(
        session: async_sessionmaker[AsyncSession], category_name: str
) -> list[str]:
    query = sa.select(Category).where(Category.name.ilike(f"%{category_name}%"))
    async with session.begin() as conn:
        result = (await conn.scalars(query)).all()
    return [cat.name for cat in result]


async def all_categories(engine: AsyncEngine, limit: int, offset: int):
    parent_category_table_name = so.aliased(Category)
    parent_category_name = (parent_category_table_name.name).label("parent_name")
    query = (
        sa.select(Category.id, Category.name, parent_category_name)
        .select_from(Category)
        .join(parent_category_table_name, Category.parent_category==parent_category_table_name.id, isouter=True)
    ).order_by(Category.created_at.desc())
    return await paginate(engine=engine, query=query, limit=limit, offset=offset)


async def delete_category_by_id(
        session: async_sessionmaker[AsyncSession], category_id: CategoryId
) -> None:
    query = sa.delete(Category).where(Category.id==category_id).returning(Category.id)
    try:
        async with session.begin() as conn:
            result = (await conn.scalar(query))
        if result is None:
            raise exceptions.CategoryNotFound
    except IntegrityError as ex:
        print(ex)
        raise exceptions.CannotDeleteParentCategory


async def get_category_by_id(
        session: async_sessionmaker[AsyncSession], category_id: CategoryId
) -> sa.Row[tuple[str, str]]:
    parent_category_table_name = so.aliased(Category)
    parent_category_name = (parent_category_table_name.name).label("parent_name")
    query = (
        sa.select(Category.name, parent_category_name)
        .where(Category.id==category_id)
        .select_from(Category)
        .join(parent_category_table_name, Category.parent_category==parent_category_table_name.id, isouter=True)
    )
    async with session.begin() as conn:
        result = (await conn.execute(query)).first()
    if result is None:
        raise exceptions.CategoryNotFound
    return result


async def update_category_by_id(
        session: async_sessionmaker[AsyncSession],
        category_id: CategoryId, payload: schemas.UpdateCategoryIn
):
    if payload.parent_category_name:
        parent_query = sa.select(Category.id).where(Category.name==payload.parent_category_name)
        async with session.begin() as conn:
            result: CategoryId | None = await conn.scalar(parent_query)
        if result is None:
            raise exceptions.InvalidParentCategoryName
    updated_query = sa.update(Category).where(Category.id==category_id).values(
        {
            Category.name: payload.name,
            Category.parent_category: result if payload.parent_category_name else None
        }
    ).returning(Category.id)
    try:
        async with session.begin() as conn:
            updated_result: CategoryId | None = await conn.scalar(updated_query)
        if updated_result is None:
            raise exceptions.CategoryNotFound
    except IntegrityError:
        raise exceptions.DuplicateCategoryName


async def publish_advertisement(
        advertisement_id: AdvertisementId,
        session: async_sessionmaker[AsyncSession],
):
    query = sa.update(Advertisement).where(Advertisement.id==advertisement_id).values(
        {
            Advertisement.published: True
        }
    )
    async with session.begin() as conn:
        await conn.execute(query)


async def unpublish_advertisement(
        advertisement_id: AdvertisementId,
        session: async_sessionmaker[AsyncSession],
):
    query = sa.update(Advertisement).where(Advertisement.id==advertisement_id).values(
        {
            Advertisement.published: False
        }
    )
    async with session.begin() as conn:
        await conn.execute(query)


async def get_all_advertisement(
        engine: AsyncEngine, limit: int, offset: int,
        phone_number: PhoneNumber | None,
        published: bool | None, is_deleted: bool | None
) -> dict:
    query = sa.select(
        Advertisement.id, Advertisement.published, Advertisement.is_deleted, User.phone_number, User.is_banned
    ).select_from(Advertisement).join(User, Advertisement.user_id==User.id).order_by(
        Advertisement.published, Advertisement.is_deleted.desc()
    ).order_by(Advertisement.created_at.desc())
    if phone_number:
        query = query.where(User.phone_number==phone_number)
    if published or published is False:
        query = query.where(Advertisement.published==published)
    if is_deleted or is_deleted is False:
        query = query.where(Advertisement.is_deleted==is_deleted)

    return await paginate(engine=engine, query=query, limit=limit, offset=offset)


async def delete_advertisement(
        advertisement_id: AdvertisementId,
        session: async_sessionmaker[AsyncSession]
):
    query = sa.delete(Advertisement).where(Advertisement.id==advertisement_id).returning(
        Advertisement.video
    )
    image_query = sa.select(AdvertisementImage.url).where(
        AdvertisementImage.advertisement_id==advertisement_id
    )
    async with session.begin() as conn:
        image_names: list[str] = list((await conn.scalars(image_query)).all())
        video_name: str | None = await conn.scalar(query)
        print(video_name)
        print(image_names)

    if video_name:
        await delete_from_s3(video_name)

    for image_name in image_names:
        await delete_from_s3(image_name)


async def get_advertisement(
        session: async_sessionmaker[AsyncSession],
        advertisement_id: AdvertisementId
) -> dict:
    query = sa.select(
        Advertisement.id, Advertisement.title, Advertisement.description, Advertisement.admin_comment,
        Advertisement.video, Advertisement.place, Advertisement.hour_price, Advertisement.day_price,
        Advertisement.week_price, Advertisement.month_price, Advertisement.published,
        Advertisement.is_deleted, AdvertisementImage.url, User.phone_number,
        Calendar.day, Category.name.label("category_name")
    ).select_from(Advertisement).join(
        AdvertisementImage, Advertisement.id==AdvertisementImage.advertisement_id
    ).join(Calendar, Advertisement.id==Calendar.advertisement_id).join(
        Category, Advertisement.category_id==Category.id
    ).join(
        User, Advertisement.user_id==User.id
    ).where(
        sa.and_(
            Advertisement.id==advertisement_id
        )
    )
    async with session.begin() as conn:
        result = (await conn.execute(query)).all()
        if not result:
            raise AdvertisementNotFound
    return {
        "id": result[0].id, "title": result[0].title, "description": result[0].description, "video": result[0].video,
        "place": result[0].place, "hour_price": result[0].hour_price, "day_price": result[0].day_price,
        "week_price": result[0].week_price, "month_price": result[0].month_price,
        "image_urls": set([image.url for image in result]), "admin_comment": result[0].admin_comment,
        "phone_number": result[0].phone_number, "published": result[0].published,
        "days": set([d.day for d in result]), "is_deleted": result[0].is_deleted,
        "category_name": result[0].category_name
    }


async def ban_user(
        phone_number: PhoneNumber,
        session: async_sessionmaker[AsyncSession],
) -> None:
    query = sa.update(User).where(User.phone_number==phone_number).values(
        {
            User.is_banned: True
        }
    ).returning(User.id)
    async with session.begin() as conn:
        user_id: UserId | None = await conn.scalar(query)
    if not user_id:
        raise UserNotFound

async def cancel_ban_user(
        phone_number: PhoneNumber,
        session: async_sessionmaker[AsyncSession],
) -> None:
    query = sa.update(User).where(User.phone_number==phone_number).values(
        {
            User.is_banned: False
        }
    ).returning(User.id)
    async with session.begin() as conn:
        user_id: UserId | None = await conn.scalar(query)
    if not user_id:
        raise UserNotFound


async def advertisement_comment(
        advertisement_id: AdvertisementId,
        session: async_sessionmaker[AsyncSession],
        comment: str
) -> None:
    query = sa.update(Advertisement).where(
        Advertisement.id==advertisement_id
    ).values(
        {
            Advertisement.admin_comment: comment,
            Advertisement.published: False
        }
    ).returning(Advertisement.id)
    async with session.begin() as conn:
        result: AdvertisementId | None = await conn.scalar(query)
    if not result:
        raise AdvertisementNotFound
