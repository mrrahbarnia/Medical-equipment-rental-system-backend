from typing import Annotated
from fastapi import Depends

from src.advertisement.exceptions import PaymentException
from src.auth.dependencies import get_current_active_user
from src.auth.models import User


async def check_subscription_fee(user: Annotated[User, Depends(get_current_active_user)]):
    if not user.has_subscription_fee:
        raise PaymentException
    return user