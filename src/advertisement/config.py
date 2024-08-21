from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    ADVERTISEMENT_VIDEO_SIZE: int
    ADVERTISEMENT_IMAGE_SIZE: int
    ADVERTISEMENT_VIDE_FORMATS: str
    ADVERTISEMENT_IMAGES_LIMIT: int
    ADVERTISEMENT_IMAGE_FORMATS: str


advertisement_settings = AuthConfig() # type: ignore
