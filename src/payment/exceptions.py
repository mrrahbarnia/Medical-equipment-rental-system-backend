from fastapi import HTTPException, status

class AlreadyPaid(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "You already paid subscription fee!"