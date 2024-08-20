import sqlalchemy as sa
import sqlalchemy.orm as so

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from src.pagination import paginate
from src.admin import schemas
from src.admin import exceptions
from src.advertisement.types import CategoryId
from src.advertisement.models import Category


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
                Category.slug: payload.slug,
                Category.parent_category: parent_category.id if parent_category else None
            }
        )
        try:
            async with session.begin() as conn:
                await conn.execute(query)
        except IntegrityError:
            raise exceptions.DuplicateCategoryName
    else:
        query = sa.insert(Category).values(
            {
                Category.name: payload.name,
                Category.slug: payload.slug
            }
        )
        try:
            async with session.begin() as conn:
                await conn.execute(query)
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
        sa.select(Category.name, Category.slug, parent_category_name)
        .select_from(Category)
        .join(parent_category_table_name, Category.parent_category==parent_category_table_name.id, isouter=True)
    )
    return await paginate(engine=engine, query=query, limit=limit, offset=offset)


async def delete_category_by_slug(
        session: async_sessionmaker[AsyncSession], category_slug: str
) -> None:
    query = sa.delete(Category).where(Category.slug==category_slug).returning(Category.id)
    async with session.begin() as conn:
        result = (await conn.scalar(query))
    if result is None:
        raise exceptions.CategoryNotFound


async def get_category_by_slug(
        session: async_sessionmaker[AsyncSession], category_slug: str
) -> sa.Row[tuple[str, str, str]]:
    parent_category_table_name = so.aliased(Category)
    parent_category_name = (parent_category_table_name.name).label("parent_name")
    query = (
        sa.select(Category.name, Category.slug, parent_category_name)
        .where(Category.slug==category_slug)
        .select_from(Category)
        .join(parent_category_table_name, Category.parent_category==parent_category_table_name.id, isouter=True)
    )
    async with session.begin() as conn:
        result = (await conn.execute(query)).first()
    if result is None:
        raise exceptions.CategoryNotFound
    return result


async def update_category_by_slug(
        session: async_sessionmaker[AsyncSession],
        category_slug: str, payload: schemas.UpdateCategoryIn
):
    if payload.parent_category_name:
        parent_query = sa.select(Category.id).where(Category.name==payload.parent_category_name)
        async with session.begin() as conn:
            result: CategoryId | None = await conn.scalar(parent_query)
        if result is None:
            raise exceptions.InvalidParentCategoryName
    updated_query = sa.update(Category).where(Category.slug==category_slug).values(
        {
            Category.name: payload.name,
            Category.slug: payload.slug,
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