from fastapi import APIRouter, status, Depends, Query
from typing import Annotated, Literal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine

from src.pagination import PaginatedResponse, pagination_query, PaginationQuerySchema
from src.database import get_engine, get_session
from src.tickets import schemas
from src.tickets import service
from src.auth.dependencies import is_admin

router = APIRouter()

@router.post(
        "/create-ticket/",
        response_model=schemas.Ticket,
        status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    input_data: schemas.Ticket,
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
) -> schemas.Ticket:
    await service.add_ticket(input_data, session)
    return input_data


@router.get(
        "/all-tickets/",
        status_code=status.HTTP_200_OK,
        response_model=PaginatedResponse[schemas.Ticket],
)
async def list_tickets(
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    pagination_info: Annotated[PaginationQuerySchema, Depends(pagination_query)],
    name__icontains: Annotated[str | None, Query(max_length=250, alias="nameIcontains")] = None,
    email__icontains: Annotated[str | None, Query(max_length=250, alias="emailIcontains")] = None
):
    response = await service.all_tickets(
        engine=engine, limit=pagination_info.limit,
        offset=pagination_info.offset, name=name__icontains, email=email__icontains
    )
    return response