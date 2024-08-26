import sqlalchemy as sa
import sqlalchemy.orm as so

from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from uuid import uuid4

from src.database import Base
from src.advertisement.types import (
    AdvertisementId, CategoryId, AdvertisementImageId, CalendarId, Price
)
from src.auth.models import User
from src.auth.types import UserId


class Advertisement(Base):
    __tablename__ = "advertisements"
    id: so.Mapped[AdvertisementId] = so.mapped_column(primary_key=True, default=uuid4)
    title: so.Mapped[str] = so.mapped_column(sa.String(250), index=True)
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    place: so.Mapped[str] = so.mapped_column(sa.Text)
    views: so.Mapped[int] = so.mapped_column(default=0)
    video: so.Mapped[str | None] = so.mapped_column(sa.String(255))
    hour_price: so.Mapped[Price | None]
    day_price: so.Mapped[Price | None]
    week_price: so.Mapped[Price | None]
    month_price: so.Mapped[Price | None]
    published: so.Mapped[bool] = so.mapped_column(default=False)
    is_deleted: so.Mapped[bool] = so.mapped_column(default=False)
    created_at: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    user_id: so.Mapped[UserId] = so.mapped_column(sa.ForeignKey(
        f"{User.__tablename__}.id", ondelete="CASCADE" # Users are not allowed to delete accounts so this method never executed
    ), index=True)
    category_id: so.Mapped[CategoryId] = so.mapped_column(sa.ForeignKey(
        "categories.id", ondelete="SET NULL"
    ), index=True)

    def __repr__(self) -> str:
        return f"{self.id} {self.title}"


class Category(Base):
    __tablename__ = "categories"
    id: so.Mapped[CategoryId] = so.mapped_column(primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(240), unique=True)
    created_at: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    parent_category: so.Mapped[CategoryId | None] = so.mapped_column(sa.ForeignKey(
        "categories.id"
    ), index=True)

    def __repr__(self) -> str:
        return f"{self.id} {self.name}"


class Calendar(Base):
    __tablename__ = "calendars"
    __table_args__ = (UniqueConstraint("advertisement_id", "day"), )
    id: so.Mapped[CalendarId] = so.mapped_column(primary_key=True, autoincrement=True)
    day: so.Mapped[date]

    advertisement_id: so.Mapped[AdvertisementId] = so.mapped_column(sa.ForeignKey(
        f"{Advertisement.__tablename__}.id", ondelete="CASCADE"
    ))

    def __repr__(self) -> str:
        return f"{self.id}, advertisement_id{self.advertisement_id}"


class AdvertisementImage(Base):
    __tablename__ = "advertisement_images"
    id: so.Mapped[AdvertisementImageId] = so.mapped_column(primary_key=True, autoincrement=True)
    url: so.Mapped[str] = so.mapped_column(sa.String(250))

    advertisement_id: so.Mapped[AdvertisementId] = so.mapped_column(sa.ForeignKey(
        f"{Advertisement.__tablename__}.id", ondelete="CASCADE"
    ), index=True)

    def __repr__(self) -> str:
        return f"{self.id}"
