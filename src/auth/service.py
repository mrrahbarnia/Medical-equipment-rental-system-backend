import httpx
import asyncio
import logging
import sqlalchemy as sa

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.auth import schemas
from src.database import get_redis_connection
from src.auth import exceptions
from src.auth import utils
from src.auth.config import auth_config
from src.auth.types import Password, UserId, PhoneNumber
from src.auth.models import User

logger = logging.getLogger("auth")


async def send_message(phone_number: PhoneNumber, subject: str):
    sms_service_url = f"{auth_config.SMS_URL}/{auth_config.SMS_URL}/sms/send.json?receptor=09134191562?sender=20006535&message=123456"
    async with httpx.AsyncClient() as client:
        r = await client.post(sms_service_url)
        # TODO: Fix this
        print(r)
    if r.status_code != 200:
        logger.error("SMS service doesn't work correctly!")


async def get_user_by_id(id: UserId, session: async_sessionmaker[AsyncSession]) -> User:
    query = sa.select(User).where(User.id == id)
    async with session.begin() as conn:
        user = (await conn.execute(query)).first()
    if not user:
        raise exceptions.UserNotFound

    return user._tuple()[0]


async def register(
        *, session: async_sessionmaker[AsyncSession], payload: schemas.RegisterIn, verification_code: str
) -> None:
    hashed_password = utils.get_password_hash(password=payload.password)
    query = sa.insert(User).values(
        {
            User.phone_number: payload.phone_number,
            User.password: hashed_password,
        }
    )
    try:
        async with session.begin() as conn:
            await conn.execute(query)
        get_redis_connection().set(
            name=f"verification_code:{verification_code}",
            value=payload.phone_number,
            ex=auth_config.VERIFICATION_CODE_LIFE_TIME_SECONDS
        )  
    except IntegrityError:
        raise exceptions.PhoneNumberAlreadyExists


async def resend_verification_code(
        *, session: async_sessionmaker[AsyncSession], phone_number: PhoneNumber, verification_code: str
) -> None:
    query = sa.select(User).where(User.phone_number==phone_number)
    async with session.begin() as conn:
        result: User | None = (await conn.scalar(query))
    if result is None:
        raise exceptions.UserNotFound
    get_redis_connection().set(
            name=f"verification_code:{verification_code}",
            value=phone_number,
            ex=auth_config.VERIFICATION_CODE_LIFE_TIME_SECONDS
        )


async def login(*, session: async_sessionmaker[AsyncSession], payload: OAuth2PasswordRequestForm) -> str:
    query = sa.select(User).where(User.phone_number == payload.username)
    async with session.begin() as conn:
        user: User | None = (await conn.scalar(query))
    if not user:
        raise exceptions.UserNotFound
    if not utils.verify_password(
        plain_password=payload.password, hashed_password=user.password
    ):
        raise exceptions.UserNotFound
    if user.is_active is False:
        raise exceptions.NotActiveUser

    return utils.encode_access_token(user_id=user.id, user_rule=user.rule)


async def verify_account(*, session: async_sessionmaker[AsyncSession], verification_code: str) -> None:
    phone_number = get_redis_connection().get(
        name=f"verification_code:{verification_code}"
    )
    if not phone_number:
        raise exceptions.InvalidVerificationCode
    query = sa.update(User).where(User.phone_number==phone_number).values({User.is_active: True})
    async with session.begin() as conn:
        await conn.execute(query)


async def change_password(
        *, session: async_sessionmaker[AsyncSession], user: User, payload: schemas.ChangePasswordIn 
) -> None: 
    if not utils.verify_password(
        plain_password=str(payload.old_password), hashed_password=user.password
    ):
        raise exceptions.WrongOldPassword
    new_hashed_password = utils.get_password_hash(payload.new_password)
    query = sa.update(User).where(User.password==user.password).values(
        {
            User.password: new_hashed_password
        }
    )
    async with session.begin() as conn:
        await conn.execute(query)


async def reset_password(
        *, session: async_sessionmaker[AsyncSession], phone_number: PhoneNumber, random_password: str
) -> bool:
    query = sa.select(User).where(User.phone_number==phone_number)
    async with session.begin() as conn:
        user: User | None = (await conn.scalar(query))
    if user is None:
        raise exceptions.UserNotFound
    get_redis_connection().set(
        name=f"reset_password:{random_password}",
        value=phone_number,
        ex=auth_config.RANDOM_PASSWORD_LIFE_TIME_SECONDS
    )
    return True


async def verify_reset_password(
        *, session: async_sessionmaker[AsyncSession], random_password: Password
) -> None:
    phone_number = get_redis_connection().get(
        name=f"reset_password:{random_password}"
    )
    if not phone_number:
        raise exceptions.InvalidRandomPassword
    new_hashed_password = utils.get_password_hash(random_password)
    query = sa.update(User).where(User.phone_number==phone_number).values({
        User.password: new_hashed_password
    })
    async with session.begin() as conn:
        await conn.execute(query)
