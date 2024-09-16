from typing import Annotated, Literal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine
from fastapi import APIRouter, status, Query, Depends

from src.database import get_session, get_engine
from src.pagination import PaginatedResponse, PaginationQuerySchema, pagination_query
from src.admin import schemas
from src.admin import service
from src.auth.dependencies import is_admin
from src.auth.types import PhoneNumber
from src.advertisement.types import AdvertisementId, CategoryId

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
    "/delete-category/{category_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_category_by_slug(
    category_id: CategoryId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.delete_category_by_id(session=session, category_id=category_id)


@router.get(
    "/get-category/{category_id}/",
    response_model=schemas.Category,
    status_code=status.HTTP_200_OK
)
async def get_category_by_id(
    category_id: CategoryId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    result = (await service.get_category_by_id(session=session, category_id=category_id))._asdict()
    return {"name":result["name"], "parent_category_name":result["parent_name"]}

@router.put(
    "/update-category/{category_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_category_by_id(
    category_id: CategoryId,
    payload: schemas.UpdateCategoryIn,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.update_category_by_id(
        session=session, category_id=category_id, payload=payload
    )


@router.get(
    "/all-advertisement/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[schemas.AllAdvertisement]
)
async def get_all_advertisement(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    pagination_info: Annotated[PaginationQuerySchema, Depends(pagination_query)],
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    phone_number: Annotated[PhoneNumber | None, Query(alias="phoneNumber")] = None,
    published: Annotated[bool | None, Query()] = None,
    is_deleted: Annotated[bool | None, Query(alias="isDeleted")] = None,
):
    response = await service.get_all_advertisement(
        engine=engine, limit=pagination_info.limit,
        offset=pagination_info.offset, phone_number=phone_number,
        published=published, is_deleted=is_deleted
    )
    return response


@router.get(
    "/publish-advertisement/{advertisement_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def publish_advertisement(
    advertisement_id: AdvertisementId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.publish_advertisement(session=session, advertisement_id=advertisement_id)


@router.get(
    "/unpublish-advertisement/{advertisement_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def unpublish_advertisement(
    advertisement_id: AdvertisementId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.unpublish_advertisement(session=session, advertisement_id=advertisement_id)


@router.patch(
        "/admin-comment/{advertisement_id}/",
        status_code=status.HTTP_204_NO_CONTENT
)
async def advertisement_comment(
    payload: schemas.AdvertisementComment,
    advertisement_id: AdvertisementId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> None:
    await service.advertisement_comment(
        session=session, advertisement_id=advertisement_id, comment=payload.admin_comment
    )


@router.delete(
    "/delete-advertisement/{advertisement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_advertisement(
    advertisement_id: AdvertisementId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    await service.delete_advertisement(session=session, advertisement_id=advertisement_id)


@router.get(
    "/get-advertisement/{advertisement_id}/",
    status_code=status.HTTP_200_OK,
    response_model=schemas.AdvertisementDetail
)
async def get_advertisement(
    advertisement_id: AdvertisementId,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
):
    result = await service.get_advertisement(
        session=session, advertisement_id=advertisement_id
    )
    return result


@router.get(
        "/ban-user/{phone_number}/",
        status_code=status.HTTP_200_OK
)
async def ban_user(
    phone_number: PhoneNumber,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> dict:
    await service.ban_user(phone_number=phone_number, session=session)
    return {"detail": "User banned successfully."}


@router.get(
        "/cancel-ban-user/{phone_number}/",
        status_code=status.HTTP_200_OK
)
async def cancel_ban_user(
    phone_number: PhoneNumber,
    is_admin: Annotated[Literal[True], Depends(is_admin)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> dict:
    await service.cancel_ban_user(phone_number=phone_number, session=session)
    return {"detail": "User ban status is set to False."}
