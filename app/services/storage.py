import logging
import uuid
from io import BytesIO
from typing import Any, Dict, IO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.exceptions.storage import FileUploadError, FileDownloadError

logger = logging.getLogger(__name__)

client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


def create_bucket():
    """Создает бакет при старте приложения, если его еще нет."""
    bucket = settings.MINIO_BUCKET
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info(f"Bucket created: {bucket}")


class StorageService:
    """Сервис для работы с MinIO хранилищем."""

    def __init__(self) -> None:
        self.client: Minio = client
        self.bucket_name: str = settings.MINIO_BUCKET
        create_bucket()

    def upload_file(
        self,
        file_data: bytes,
        original_filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """Загружает файл в MinIO."""
        ext = original_filename.split(".")[-1]
        object_name = f"{uuid.uuid4()}.{ext}"

        try:
            file_stream = BytesIO(file_data)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type,
            )

            logger.info(f"File uploaded: {object_name} ({len(file_data)} bytes)")

            return {
                "status": "success",
                "bucket": self.bucket_name,
                "object_name": object_name,
                "original_filename": original_filename,
                "size": len(file_data),
            }
        except S3Error as err:
            logger.error(f"Failed to upload file: {original_filename}")
            raise FileUploadError(
                f"Не удалось загрузить файл '{original_filename}' в хранилище."
            ) from err

    def get_file(self, object_name: str) -> bytes:
        """Скачивает файл из MinIO."""
        try:
            response: IO[bytes] = self.client.get_object(
                bucket_name=self.bucket_name, object_name=object_name
            )

            file_data: bytes = response.read()
            response.close()

            logger.debug(f"File retrieved: {object_name} ({len(file_data)} bytes)")

            return file_data
        except S3Error as err:
            logger.error(f"Failed to retrieve file: {object_name}")
            raise FileDownloadError(
                f"Не удалось получить файл '{object_name}' из хранилища."
            ) from err
       