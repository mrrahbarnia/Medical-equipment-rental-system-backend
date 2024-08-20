from functools import lru_cache
from redis import Redis
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from sqlalchemy.types import DateTime, INTEGER, String, UUID, Numeric
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession

from src.constants import DB_NAMING_CONVENTION
from src.config import settings
from src.auth import types as auth_types
from src.advertisement import types as advertisement_types

POSTGRES_URL = str(settings.POSTGRES_ASYNC_URL)

engine: AsyncEngine = create_async_engine(POSTGRES_URL)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
    type_annotation_map = {
        auth_types.UserId: INTEGER,
        auth_types.PhoneNumber: String,
        auth_types.Password: String,
        advertisement_types.AdvertisementId: UUID,
        advertisement_types.CategoryId: INTEGER,
        advertisement_types.PriceId: INTEGER,
        advertisement_types.Price: Numeric,
        advertisement_types.CalendarId: INTEGER,
        datetime: DateTime(timezone=True),
    }


@lru_cache
def get_engine() -> AsyncEngine:
    return engine


async def get_session() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def get_redis_connection() -> Redis:
    return Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )