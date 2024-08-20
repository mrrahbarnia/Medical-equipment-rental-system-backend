from fastapi import HTTPException, status


class PaymentException(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_402_PAYMENT_REQUIRED
        self.detail = "You have to pay the subscription fee first!"