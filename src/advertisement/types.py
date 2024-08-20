from enum import Enum
from typing import  NewType
from decimal import Decimal
from uuid import UUID

class Period(Enum):
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"

AdvertisementId = NewType("AdvertisementId", UUID)
CategoryId = NewType("CategoryId", int)
PriceId = NewType("PriceId", int)
Price = NewType("Price", Decimal)
CalendarId = NewType("CalendarId", int)

