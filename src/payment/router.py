from typing import Annotated
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import get_session
from src.payment import service
from src.auth.dependencies import get_current_active_user
from src.auth.models import User

router = APIRouter()


@router.get(
    "/add-subscription-fee/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def add_subscription_fee(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[async_sessionmaker[AsyncSession], Depends(get_session)]
):
    await service.add_subscription_fee(session=session, user=current_user)