from fastapi import HTTPException, status

from src.config import settings
from src.advertisement.config import advertisement_settings


class PaymentException(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_402_PAYMENT_REQUIRED
        self.detail = "You have to pay the subscription fee first!"


class InvalidCategoryName(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "There is no category with the provided name!"


class LargeVideoFile(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Video file size must be maximum {advertisement_settings.ADVERTISEMENT_VIDEO_SIZE}!"


class LargeImageFile(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Image file size must be maximum {advertisement_settings.ADVERTISEMENT_IMAGE_SIZE}!"


class InvalidVideoFormat(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Video format must be in {advertisement_settings.ADVERTISEMENT_VIDE_FORMATS}!"


class InvalidImageFormat(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Image format must be in {advertisement_settings.ADVERTISEMENT_IMAGE_FORMATS}!"


class AdvertisementImageLimit(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Advertisement at least has {advertisement_settings.ADVERTISEMENT_IMAGES_LIMIT} images!"


class DuplicateSelectedDays(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Selected days must be unique per each advertisement!"


class NotOwner(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = "You only can delete advertisement which is your's and not deleted before!"


class AdvertisementNotFound(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "Advertisement not found!"


class DailyRateLimit(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = f"Daily rate limit exceeded!({settings.REQUEST_PER_DAY} PER DAY)"


class HourlyRateLimit(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = f"Hourly rate limit exceeded!({settings.REQUEST_PER_HOUR} PER HOUR)"
