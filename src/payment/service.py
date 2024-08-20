import logging
import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.payment import exceptions
from src.auth.models import User

logger = logging.getLogger("payment")


async def add_subscription_fee(
        session: async_sessionmaker[AsyncSession], user: User
) -> None:
    if user.has_subscription_fee:
        raise exceptions.AlreadyPaid
    query = sa.update(User).where(User.id==user.id).values(
        {
            User.has_subscription_fee: True
        }
    )
    async with session.begin() as conn:
        await conn.execute(query)
    logger.info("Paid subscription fee.")
