from typing import Annotated
from pydantic import Field, field_validator

from src.schemas import CustomBaseModel
from src.config import settings


class AdvertisementOut(CustomBaseModel):
    title: Annotated[str, Field(max_length=250)]
    description: str
    place: str
    video: str | None = None

    @field_validator("video", mode="after")
    @classmethod
    def set_video_url(cls, value: str) -> str:
        return f"{settings.S3_API}/{value}"
