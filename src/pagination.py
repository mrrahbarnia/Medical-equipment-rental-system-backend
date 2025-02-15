import sqlalchemy as sa

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncEngine
from pydantic import BaseModel
from typing import TypeVar, Generic, Annotated

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    count: int
    items: list[T]


class PaginationQuerySchema(BaseModel):
    limit: int
    offset: int


async def pagination_query(
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(alias="per-page")] = 10
) -> PaginationQuerySchema:
    """
    Dependency for getting page and per_page from
    query parameters and convert them to limit offset.
    """
    limit: int = per_page
    offset: int = (page - 1) * per_page
    return PaginationQuerySchema(limit=limit, offset=offset)


async def paginate(
        *, engine: AsyncEngine, query: sa.Select, limit: int, offset: int
) -> dict:
    """
    Helper function for pagination.
    """
    count_query: sa.Select = sa.Select(sa.func.count()).select_from(query.subquery())
    paginated_query: sa.Select = query.limit(limit).offset(offset)
    async with engine.begin() as conn:
        result = {
            "count": ((await conn.execute(count_query)).first())[0], # type: ignore
            "items": (await conn.execute(paginated_query)).all()
        }
    return result
