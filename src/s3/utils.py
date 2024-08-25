from typing import BinaryIO
from aiobotocore.session import get_session # type: ignore

from src.config import settings


async def upload_to_s3(file: BinaryIO, unique_filename: str):
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
    ) as client:
        await client.put_object(
            Bucket=settings.BUCKET_NAME,
            Key=unique_filename,
            Body=file
        )


async def delete_from_s3(filename: str):
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
    ) as client:
        await client.delete_object(
            Bucket=settings.BUCKET_NAME, Key=filename
        )