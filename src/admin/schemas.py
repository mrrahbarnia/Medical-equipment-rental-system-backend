from pydantic import BaseModel, Field, computed_field
from typing import Annotated

from src.schemas import CustomBaseModel
from src.advertisement import types
from src.advertisement.utils import create_slug


class Category(CustomBaseModel):
    name: Annotated[str, Field(max_length=240)]
    parent_category_name: Annotated[str | None, Field(alias="parentCategoryName")] = None

    @computed_field # type: ignore
    @property
    def slug(self) -> str:
        return create_slug(self.name)


class AllCategories(CustomBaseModel):
    name: str
    slug: str
    parent_name: Annotated[str | None, Field(alias="parentName")] = None


class UpdateCategoryIn(CustomBaseModel):
    name: str | None
    parent_category_name: Annotated[str | None, Field(alias="parentCategoryName")] = None

    @computed_field # type: ignore
    @property
    def slug(self) -> str:
        if self.name:
            return create_slug(self.name)
