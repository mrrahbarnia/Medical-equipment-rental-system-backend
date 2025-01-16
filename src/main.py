import logging
from logging.config import dictConfig

from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from src.config import LogConfig, app_configs
from src.auth import router as auth_router
from src.advertisement import router as advertisement_router
from src.admin import router as admin_router
from src.payment import router as payment_router
from src.tickets import router as ticket_router

logger = logging.getLogger("root")


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    dictConfig(LogConfig().model_dump())
    logger.info("App is running...")
    yield


app = FastAPI(**app_configs, lifespan=lifespan)

origins = [
    "http://127.0.0.1",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(router=auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(router=advertisement_router.router, prefix="/advertisement", tags=["advertisement"])
app.include_router(router=admin_router.router, prefix="/admin", tags=["admin"])
app.include_router(router=payment_router.router, prefix="/payment", tags=["payment"])
app.include_router(router=ticket_router.router, prefix="/tickets", tags=["tickets"])
