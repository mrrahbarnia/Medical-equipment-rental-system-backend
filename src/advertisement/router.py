from typing import Annotated

from fastapi import APIRouter, status, UploadFile, File, Query, Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from src.database import get_session, get_engine
from src.pagination import PaginatedResponse, pagination_query, PaginationQuerySchema
from src.advertisement import service
from src.advertisement import schemas
from src.advertisement.types import AdvertisementId
from src.advertisement.dependencies import check_subscription_fee
from src.auth.dependencies import get_current_active_user
from src.auth.models import User

router = APIRouter()


@router.post(
    "/add-advertisement/",
    status_code=status.HTTP_201_CREATED
)
async def add_advertisement(
    payload: schemas.AdvertisementIn,
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(check_subscription_fee)],
    images: list[UploadFile],
    video: UploadFile | None = None,
) -> dict:
    await service.add_advertisement(
        session=session,
        user=current_user,
        payload=payload,
        video=video,
        images=images
    )
    return {
        "title": payload.title, "description": payload.description
    }


@router.get(
    "/published-advertisement/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[schemas.PublishedAdvertisement],
)
async def get_published_advertisement(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    pagination_info: Annotated[PaginationQuerySchema, Depends(pagination_query)],
    text__icontains: Annotated[str | None, Query(alias="textIcontains", max_length=250)] = None,
    place__icontains: Annotated[str | None, Query(alias="placeIcontains")] = None,
    hour_price__range: Annotated[str | None, Query(alias="hourPriceRange")] = None,
    day_price__range: Annotated[str | None, Query(alias="dayPriceRange")] = None,
    week_price__range: Annotated[str | None, Query(alias="weekPriceRange")] = None,
    month_price__range: Annotated[str | None, Query(alias="monthPriceRange")] = None,
    category_name: Annotated[str | None, Query(alias="categoryName")] = None
):
    response = await service.get_published_advertisement(
        engine=engine, limit=pagination_info.limit, offset=pagination_info.offset,
        text__icontains=text__icontains, place__icontains=place__icontains,
        hour_price__range=hour_price__range, day_price__range=day_price__range,
        week_price__range=week_price__range, month_price__range=month_price__range,
        category_name=category_name
    )
    return response

@router.get(
    "/list/my-advertisement/",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.MyAdvertisement]
)
async def list_my_advertisement(
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await service.list_my_advertisement(session=session, user=current_user)
    return result


@router.delete(
    "/delete/my-advertisement/{advertisement_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_advertisement(
    advertisement_id: AdvertisementId,
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    await service.delete_my_advertisement(
        session=session, user=current_user, advertisement_id=advertisement_id
    )


@router.get(
    "/get-advertisement/{advertisement_id}/",
    status_code=status.HTTP_200_OK,
    response_model=schemas.AdvertisementDetail
)
async def get_advertisement(
    advertisement_id: AdvertisementId,
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> dict:
    result = await service.get_advertisement(
        session=session, advertisement_id=advertisement_id
    )
    return result


@router.get(
    "/show-phone-number/{advertisement_id}/",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ShowPhoneNumber
)
async def show_phone_number(
    advertisement_id: AdvertisementId,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> dict:
    phone_number = await service.show_phone_number(
        session=session, user=current_user, advertisement_id=advertisement_id
    )
    return {"phoneNumber": phone_number}


@router.get(
    "/get-my-advertisement/{advertisement_id}/",
    status_code=status.HTTP_200_OK,
    response_model=schemas.AdvertisementDetail
)
async def get_my_advertisement(
    advertisement_id: AdvertisementId,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
) -> dict:
    result = await service.get_my_advertisement(
        session=session, user=current_user, advertisement_id=advertisement_id
    )
    return result


@router.put(
    "/update-my-advertisement/{advertisement_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def update_my_advertisement(
    advertisement_id: AdvertisementId,
    payload: schemas.AdvertisementUpdate,
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    video: UploadFile | None = None,
    images: Annotated[list[UploadFile], File()] = None # type: ignore
) -> None:
    await service.update_my_advertisement(
        session=session,
        advertisement_id=advertisement_id,
        user=current_user,
        payload=payload,
        video=video,
        images=images
    )


@router.get(
    "/list/most-viewed-ads/",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.MostViewedAds]
)
async def get_most_viewed_ads(
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
):
    result = await service.get_most_viewed_ads(session=session)
    return result


@router.get(
    "/list/recent-ads/",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.RecentAds]
)
async def get_recent_ads(
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
):
    result = await service.get_recent_ads(session=session)
    return result