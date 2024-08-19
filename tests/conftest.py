import pytest
import pytest_asyncio
import asyncio
import sqlalchemy as sa

from functools import lru_cache
from typing import AsyncGenerator, Final, Generator
from httpx import AsyncClient, ASGITransport
from async_asgi_testclient import TestClient # type: ignore
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker

from src.database import Base, get_session
from src.config import settings
from src.main import app
from src.auth.utils import get_password_hash
from src.auth.models import User
from src.auth.types import Password

TEST_DB_URL: Final[str] = str(settings.POSTGRES_TEST_ASYNC_URL)
test_engine = create_async_engine(TEST_DB_URL)


@lru_cache
def override_get_engine() -> AsyncEngine:
    return test_engine

def override_get_session() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, expire_on_commit=False)

app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(TEST_DB_URL)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _database_objects(db_engine: AsyncEngine):
    try:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield
    finally:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_admin_user(db_engine: AsyncEngine):
    hashed_password = get_password_hash(Password("mM@123456"))
    query = sa.insert(User).values({
        User.phone_number: "09132222222",
        User.password: hashed_password,
        User.rule: "admin",
        User.is_active: True
    })
    async with db_engine.begin() as transaction:
        await transaction.execute(query)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[TestClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", "8000")), base_url="http://test") as client: # type: ignore
        yield client