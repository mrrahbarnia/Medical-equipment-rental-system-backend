from typing import  NewType
from decimal import Decimal
from uuid import UUID

AdvertisementId = NewType("AdvertisementId", UUID)
CategoryId = NewType("CategoryId", int)
Price = NewType("Price", Decimal)
CalendarId = NewType("CalendarId", int)
AdvertisementImageId = NewType("AdvertisementImageId", int)

