# import aioredis

from typing import AsyncGenerator
from functools import lru_cache
# from aioredis import Redis
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from sqlalchemy.types import DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker

from src.constants import DB_NAMING_CONVENTION
from src.config import settings

POSTGRES_URL = str(settings.POSTGRES_ASYNC_URL)
# REDIS_URL = str(settings.REDIS_URL)

engine: AsyncEngine = create_async_engine(POSTGRES_URL, echo=True)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


@lru_cache
def get_engine() -> AsyncEngine:
    return engine


async def session() -> AsyncGenerator:
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker.begin() as session:
        yield session


# async def get_redis_connection() -> Redis:
#     return await aioredis.from_url(REDIS_URL, decode_response=True)