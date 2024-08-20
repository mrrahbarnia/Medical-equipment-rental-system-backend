from typing import Annotated, Literal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine
from fastapi import APIRouter, status, Depends

from src.database import get_session, get_engine
from src.pagination import PaginatedResponse, PaginationQuerySchema, pagination_query
from src.admin import schemas
from src.admin import service
from src.auth.dependencies import is_admin

router = APIRouter()


@router.post(
    "/create-categories/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Category
)
async def create_category(
    payload: schemas.Category,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
) -> schemas.Category:
    await service.add_category(session=session, payload=payload)
    return payload


@router.get(
    "/search-categories/",
    status_code=status.HTTP_200_OK,
    response_model=list[str]
)
async def search_category_by_name(
    category_name: str,
    # is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
):
    result = await service.search_category_by_name(session=session, category_name=category_name)
    return result


@router.get(
    "/all-categories/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[schemas.AllCategories],
)
async def list_categories(
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    pagination_info: Annotated[PaginationQuerySchema, Depends(pagination_query)]
):
    response = await service.all_categories(
        engine=engine, limit=pagination_info.limit, offset=pagination_info.offset
    )
    return response


@router.delete(
    "/delete-category/{category_slug}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_category_by_slug(
    category_slug: str,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.delete_category_by_slug(session=session, category_slug=category_slug)


@router.get(
    "/get-category/{category_slug}/",
    response_model=schemas.Category,
    status_code=status.HTTP_200_OK
)
async def get_category_by_slug(
    category_slug: str,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    result = (await service.get_category_by_slug(session=session, category_slug=category_slug))._asdict()
    return {"name":result["name"], "parent_category_name":result["parent_name"]}

@router.put(
    "/update-category/{category_slug}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_category_by_slug(
    category_slug: str,
    payload: schemas.UpdateCategoryIn,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.update_category_by_slug(
        session=session, category_slug=category_slug, payload=payload
    )
