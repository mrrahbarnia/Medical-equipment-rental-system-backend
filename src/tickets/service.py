import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

from src.pagination import paginate
from src.tickets.models import Ticket
from src.tickets.schemas import Ticket as TicketSchema


async def add_ticket(
        input_data: TicketSchema, session: async_sessionmaker[AsyncSession]
) -> None:
    query = sa.insert(Ticket).values({
        Ticket.name: input_data.name,
        Ticket.email: input_data.email,
        Ticket.message: input_data.message
    })
    async with session.begin() as conn:
        await conn.execute(query)


async def all_tickets(
        *, engine: AsyncEngine, limit: int, offset: int,
        name: str | None, email: str | None
) -> dict:
    query = sa.select(Ticket.email, Ticket.name, Ticket.message)
    if name:
        query = query.where(Ticket.name.ilike(f"%{name}%"))
    if email:
        query = query.where(Ticket.email.ilike(f"%{email}%"))

    result = await paginate(
        engine=engine, query=query, limit=limit, offset=offset
    )
    return result