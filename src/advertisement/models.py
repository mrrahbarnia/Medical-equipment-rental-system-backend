import sqlalchemy as sa
import sqlalchemy.orm as so

from datetime import datetime, date
from uuid import uuid4

from src.database import Base
from src.advertisement.types import (
    AdvertisementId, CategoryId, PriceId,
    Period, CalendarId, Price as PriceType
)
from src.auth.models import User
from src.auth.types import UserId


class Advertisement(Base):
    __tablename__ = "advertisements"
    id: so.Mapped[AdvertisementId] = so.mapped_column(primary_key=True, default=uuid4)
    title: so.Mapped[str] = so.mapped_column(sa.String(250), index=True)
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    image: so.Mapped[str | None] = so.mapped_column(sa.String(255))
    video: so.Mapped[str | None] = so.mapped_column(sa.String(255))
    approved: so.Mapped[bool] = so.mapped_column(default=False)
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
    slug: so.Mapped[str] = so.mapped_column(sa.String(250), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    parent_category: so.Mapped[CategoryId | None] = so.mapped_column(sa.ForeignKey(
        "categories.id", ondelete="SET NULL"
    ), index=True)

    def __repr__(self) -> str:
        return f"{self.id} {self.name}"


class Price(Base):
    __tablename__ = "prices"
    id: so.Mapped[PriceId] = so.mapped_column(primary_key=True, autoincrement=True)
    period: so.Mapped[Period]
    price: so.Mapped[PriceType]

    advertisement_id: so.Mapped[AdvertisementId] = so.mapped_column(sa.ForeignKey(
        f"{Advertisement.__tablename__}.id", ondelete="CASCADE"
    ))

    def __repr__(self) -> str:
        return f"{self.id}, advertisement_id{self.advertisement_id}"


class Calendar(Base):
    __tablename__ = "calendars"
    id: so.Mapped[CalendarId] = so.mapped_column(primary_key=True, autoincrement=True)
    day: so.Mapped[date]

    advertisement_id: so.Mapped[AdvertisementId] = so.mapped_column(sa.ForeignKey(
        f"{Advertisement.__tablename__}.id", ondelete="CASCADE"
    ))

    def __repr__(self) -> str:
        return f"{self.id}, advertisement_id{self.advertisement_id}"
