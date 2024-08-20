from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    ADVERTISEMENT_VIDEO: int
    ADVERTISEMENT_IMAGE: int


auth_config = AuthConfig() # type: ignore
