import json

from decimal import Decimal
from datetime import date
from typing import Annotated, Self, Any
from pydantic import BaseModel, ValidationInfo, Field, field_validator, model_validator

from src.schemas import CustomBaseModel
from src.config import settings
from src.advertisement import types


class AdvertisementOut(CustomBaseModel):
    title: Annotated[str, Field(max_length=250)]
    description: str
    place: str


class AdvertisementIn(AdvertisementOut):
    category_name: Annotated[str, Field(alias="categoryName")]
    days: list[date]
    hour_price: Annotated[Decimal | None, Field(alias="hourPrice")] = None
    day_price: Annotated[Decimal | None, Field(alias="dayPrice")] = None
    week_price: Annotated[Decimal | None, Field(alias="weekPrice")] = None
    month_price: Annotated[Decimal | None, Field(alias="monthPrice")] = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value) -> Any:
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

    @model_validator(mode="after")
    def validate_prices(self) -> Self:
        if (self.hour_price == 0 or self.hour_price is None) and \
            (self.day_price == 0 or self.day_price is None) and \
                (self.week_price == 0 or self.week_price is None) and \
                    (self.month_price == 0 or self.month_price is None):
            raise ValueError("Was not assign any price!")
        return self

    @field_validator("week_price")
    @classmethod
    def validate_week_price(cls, value: Decimal, validated_data: ValidationInfo) -> Decimal:
        data = validated_data.data
        if value and "days" in data and len(data.get("days")) < 7: # type: ignore
            raise ValueError("Selected days must at least be 7 days for setting week price!")
        return value
    
    @field_validator("month_price")
    @classmethod
    def validate_month_price(cls, value: Decimal, validated_data: ValidationInfo) -> Decimal:
        data = validated_data.data
        if value and "days" in data and len(data.get("days")) < 30: # type: ignore
            raise ValueError("Selected days must at least be 30 days for setting month price!")
        return value


class PublishedAdvertisement(BaseModel):
    id: types.AdvertisementId
    title: Annotated[str, Field(max_length=250)]
    description: str
    place: str
    image: str | None = None

    @field_validator("image", mode="after")
    @classmethod
    def set_image_url(cls, image: str | None) -> str | None:
        if image:
            return f"{settings.S3_API}/{image}"
        return None


