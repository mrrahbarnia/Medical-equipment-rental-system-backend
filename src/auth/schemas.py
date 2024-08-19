import re

from typing import Annotated
from pydantic import (
    BaseModel, ConfigDict, model_validator, Field, field_validator
)

# from src.config import settings
from src.schemas import CustomBaseModel
from src.auth.config import auth_config
from src.auth.types import Password, PhoneNumber

PASSWORD_PATTERN = auth_config.PASSWORD_PATTERN


class RegisterOut(CustomBaseModel):
    phone_number: Annotated[PhoneNumber, Field(alias="phoneNumber")]


class RegisterIn(RegisterOut):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "phoneNumber": "09131111111",
                "password": "mM@123456",
                "confirmPassword": "mM@123456",
            }
        ]
    })
    password: Password
    confirm_password: Annotated[Password, Field(alias="confirmPassword")]

    @model_validator(mode="after")
    def validate_passwords(self):
        password = self.password
        confirm_password = self.confirm_password

        if password is not None and confirm_password is not None and password != confirm_password:
            raise ValueError("Passwords don't match!")
        return self

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: Password) -> Password:
        if not re.match(PASSWORD_PATTERN, value):
            raise ValueError(
                "Password must contain at least 8 chars, "
                "one lower character, "
                "one upper character, "
                "digit or "
                "special symbol"
            )
        return value


class LoginIn(BaseModel):
    username: PhoneNumber
    password: Password


class LoginOut(BaseModel):
    username: str
    access_token: str
    token_type: str


class VerificationIn(CustomBaseModel):
    verification_code: str = Field(alias="verificationCode")


class ResendVerificationCode(BaseModel):
    phone_number: Annotated[PhoneNumber, Field(alias="phoneNumber")]


class ChangePasswordIn(CustomBaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {   
                "oldPassword": "oldPassword",
                "newPassword": "mM@123456",
                "confirmPassword": "mM@123456",
            }
        ]
    })
    old_password: Password = Field(alias="oldPassword")
    new_password: Password = Field(alias="newPassword")
    confirm_password: Password = Field(alias="confirmPassword")

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password_pattern(cls, new_password: Password) -> Password:
        if not re.match(PASSWORD_PATTERN, new_password):
            raise ValueError(
                "Has minimum 8 characters in length",
                "At least one uppercase English letter",
                "At least one lowercase English letter",
                "At least one digit",
                "At least one special character"
            )
        return new_password

    @model_validator(mode="after")
    def validate_passwords(self):
        new_password = self.new_password
        confirm_password = self.confirm_password
        if new_password is not None and confirm_password is not None and new_password != confirm_password:
            raise ValueError("Passwords don't match!")
        return self


class ResetPasswordIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "phoneNumber": "09131111111"
            }
        ]
    })
    phone_number: Annotated[PhoneNumber, Field(alias="phoneNumber")]


class VerifyResetPasswordIn(CustomBaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "randomPassword": "12345678"
            }
        ]
    })
    random_password: Annotated[Password, Field(alias="randomPassword")]
