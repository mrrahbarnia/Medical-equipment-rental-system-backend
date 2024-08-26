from pydantic import BaseModel, Field
from typing import Annotated

from src.schemas import CustomBaseModel
from src.advertisement import types
from src.advertisement.schemas import AdvertisementDetail as UsersAdvertisementDetail
from src.auth import types as auth_types


class Category(CustomBaseModel):
    name: Annotated[str, Field(max_length=240)]
    parent_category_name: Annotated[str | None, Field(alias="parentCategoryName")] = None


class AllCategories(CustomBaseModel):
    name: str
    parent_name: Annotated[str | None, Field(alias="parentName")] = None


class UpdateCategoryIn(CustomBaseModel):
    name: str | None
    parent_category_name: Annotated[str | None, Field(alias="parentCategoryName")] = None


class AllAdvertisement(BaseModel):
    id: types.AdvertisementId
    phone_number: auth_types.PhoneNumber
    published: bool
    is_deleted: Annotated[bool, Field(alias="isDeleted", validation_alias="is_deleted")]


class AdvertisementDetail(UsersAdvertisementDetail):
    published: bool
    is_deleted: Annotated[bool, Field(alias="isDeleted")]