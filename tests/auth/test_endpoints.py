import pytest

from fastapi import status
from async_asgi_testclient import TestClient # type: ignore

from src.database import get_redis_connection

pytestmark = pytest.mark.asyncio


async def test_register(client: TestClient):
    payload = {
        "phoneNumber": "09131111111",
        "password": "mM@#12345678n",
        "confirmPassword": "mM@#12345678n"
    }
    response = await client.post("/auth/register/", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"phoneNumber": "09131111111"}


@pytest.mark.parametrize(
        "entered_data, expected_status",
        [
            (
                {
                    "phoneNumber": "09131111111",
                    "password": "1mM@",
                    "confirmPassword": "1mM@"
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "phoneNumber": "09131111111",
                    "password": "12345678",
                    "confirmPassword": "12345678"
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "phoneNumber": "09131111111",
                    "password": "mM@mmmmm",
                    "confirmPassword": "mM@mmmmm"
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            (
                {
                    "phoneNumber": "09131111111",
                    "password": "123MMmmm",
                    "confirmPassword": "123MMmmm"
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),

            
        ]
)
async def test_register_with_invalid_data(client: TestClient, entered_data, expected_status):
    response = await client.post("/auth/register/", json=entered_data)
    assert response.status_code == expected_status


async def test_register_with_duplicate_email(client: TestClient):
    payload = {
        "phoneNumber": "09131111111",
        "password": "123MMmmm@@",
        "confirmPassword": "123MMmmm@@"
    }
    response = await client.post("/auth/register/", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {'detail': 'Phone number already exists'}


async def test_verify_account_with_invalid_verification_code(client: TestClient):
    payload = {
        "verificationCode": "12345678"
    }
    response = await client.post("/auth/verify-account/", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Verification code is invalid, get a new one"}


async def test_verify_account_with_valid_verification_code(client: TestClient):
    r = get_redis_connection()
    result_list: list[str] = r.keys(pattern="verification_code*") # type: ignore
    payload = {
        "verificationCode": result_list[0].split(":")[1]
    }
    response = await client.post("/auth/verify-account/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "Account verified successfully"}


async def test_verification_code_with_not_existing_account(client: TestClient):
    payload = {
        "phoneNumber": "09131111112"
    }
    response = await client.post("/auth/resend/verification-code/", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'There is no active account with the provided info'}


async def test_verification_code_with_existing_account(client: TestClient):
    payload = {
        "phoneNumber": "09131111111"
    }
    response = await client.post("/auth/resend/verification-code/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "Verification code was resent."}


async def test_login_with_not_existing_account(client: TestClient):
    payload = {
        "username": "test1",
        "password": "invalid12345"
    }
    response = await client.post(
        "/auth/login/", headers={"Content-Type": "application/x-www-form-urlencoded"}, data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "There is no active account with the provided info"}


async def test_admin_login_successfully(client: TestClient):
    payload = {
        "username": "09132222222",
        "password": "mM@123456"
    }
    response = await client.post(
        "/auth/login/", headers={"Content-Type": "application/x-www-form-urlencoded"}, data=payload
    )
    assert response.status_code == status.HTTP_200_OK
    access_token = response.json()["access_token"]
    assert access_token is not None
    return access_token


async def test_reset_password_with_not_existing_phone_number(client: TestClient):
    payload = {
        "phoneNumber": "09133333333"
    }
    response = await client.post("/auth/reset-password/", json=payload)

    assert response.json() == {'detail': 'There is no active account with the provided info'}
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_reset_password_with_existing_phone_number_successfully(client: TestClient):
    payload = {
        "phoneNumber": "09131111111"
    }
    response = await client.post("/auth/reset-password/", json=payload)

    assert response.json() == {"detail": "Temporary password was sent for you."}
    assert response.status_code == status.HTTP_200_OK


async def test_verify_reset_password_with_invalid_data(client: TestClient):
    payload = {
        "randomPassword": "12345678"
    }
    response = await client.post("/auth/reset-password/verify/", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Random Password is invalid, get a new one'}


async def test_verify_reset_password_with_valid_data_successfully(client: TestClient):
    r = get_redis_connection()
    result_list: list[str] = r.keys(pattern="reset_password*") # type: ignore
    payload = {
        "randomPassword": result_list[0].split(":")[1]
    }
    response = await client.post("/auth/reset-password/verify/", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "Password reset successfully.Change it to your favorite."}

