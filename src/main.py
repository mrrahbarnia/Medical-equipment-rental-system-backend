import logging
from logging.config import dictConfig

from typing import AsyncGenerator
from fastapi import FastAPI
from contextlib import asynccontextmanager


from src.config import LogConfig, app_configs

logger = logging.getLogger("root")


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    dictConfig(LogConfig().model_dump())
    logger.info("App is running...")
    yield


app = FastAPI(**app_configs, lifespan=lifespan)
# app.include_router(router=auth_router.router, prefix="/auth", tags=["auth"])
