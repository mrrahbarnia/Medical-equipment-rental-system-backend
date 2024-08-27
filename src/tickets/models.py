import sqlalchemy as sa
import sqlalchemy.orm as so

from datetime import datetime

from src.database import Base
from src.tickets.types import TicketId

class Ticket(Base):
    __tablename__ = "tickets"

    id: so.Mapped[TicketId] = so.mapped_column(primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(250), index=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(250), index=True)
    message: so.Mapped[str] = so.mapped_column(sa.Text)
    created_at: so.Mapped[datetime] = so.mapped_column(default=sa.func.now())

    def __repr__(self) -> str:
        return self.name