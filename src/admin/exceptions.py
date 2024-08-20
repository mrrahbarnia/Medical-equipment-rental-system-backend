from fastapi import HTTPException, status


class InvalidParentCategoryName(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "There is no category with the provided parent category name!"


class DuplicateCategoryName(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = "Category name field is unique!"


class CategoryNotFound(HTTPException):
    def __init__(self) -> None:
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "There is no category with the provided info!"
