import sqlalchemy as sa
import sqlalchemy.orm as so

from datetime import datetime

from src.database import Base
from src.auth.types import UserId, PhoneNumber


class User(Base):
    __tablename__ = "users"
    id: so.Mapped[UserId] = so.mapped_column(primary_key=True, autoincrement=True)
    phone_number: so.Mapped[PhoneNumber] = so.mapped_column(sa.String(12), unique=True)
    rule: so.Mapped[str] = so.mapped_column(sa.String(30), default="user")
    password: so.Mapped[str] = so.mapped_column()
    has_subscription_fee: so.Mapped[bool] = so.mapped_column(default=False)
    is_active: so.Mapped[bool] = so.mapped_column(default=False)
    created_at: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    def __repr__(self) -> str:
        return f"User {self.id} {self.phone_number}"
