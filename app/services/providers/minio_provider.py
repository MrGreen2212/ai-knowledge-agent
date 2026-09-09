"""
MinIO реализация StorageProvider.

Конкретная реализация интерфейса StorageProvider для работы с MinIO.
"""

import logging
import uuid
from io import BytesIO
from typing import Any, Dict, Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.exceptions.providers import (
    StorageConnectionError,
    StorageDeleteError,
    StorageDownloadError,
    StorageUploadError,
)

from .storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class MinIOProvider(StorageProvider):
    """
    MinIO реализация StorageProvider.

    Использует MinIO для хранения и получения файлов.
    Реализует интерфейс StorageProvider, следуя принципу Liskov Substitution Principle (LSP).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: bool = False,
    ):
        """
        Инициализирует MinIO провайдер.

        Args:
            endpoint: Адрес MinIO сервера
            access_key: Ключ доступа
            secret_key: Секретный ключ
            bucket_name: Название бакета
            secure: Использовать ли HTTPS

        Raises:
            StorageConnectionError: Если не удалось инициализировать MinIO
        """
        try:
            self.client = Minio(
                endpoint=endpoint or settings.MINIO_ENDPOINT,
                access_key=access_key or settings.MINIO_ACCESS_KEY,
                secret_key=secret_key or settings.MINIO_SECRET_KEY,
                secure=secure,
            )
            self.bucket_name = bucket_name or settings.MINIO_BUCKET
            self._ensure_bucket()
            logger.info(f"MinIOProvider initialized with bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO: {e}")
            raise StorageConnectionError(f"Не удалось инициализировать MinIO: {e}")

    def _ensure_bucket(self) -> None:
        """Создает бакет, если его еще нет."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket created: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise StorageConnectionError(f"Ошибка при проверке/создании бакета: {e}")

    def upload_file(
        self,
        file_data: bytes,
        original_filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """
        
        Загружает файл в MinIO.

        Args:
            file_data: Содержимое файла в байтах
            original_filename: Оригинальное имя файла
            content_type: MIME-тип файла

        Returns:
            Словарь с информацией о загруженном файле

        Raises:
            StorageUploadError: Если произошла ошибка при загрузке файла
        """
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
            raise StorageUploadError(
                f"Не удалось загрузить файл '{original_filename}' в хранилище."
            ) from err

    def get_file(self, object_name: str) -> bytes:
        """
        Скачивает файл из MinIO.

        Args:
            object_name: Имя объекта в хранилище

        Returns:
            Содержимое файла в байтах

        Raises:
            StorageDownloadError: Если произошла ошибка при скачивании файла
        """
        try:
            response = self.client.get_object(bucket_name=self.bucket_name, object_name=object_name)

            file_data: bytes = response.read()
            response.close()

            logger.debug(f"File retrieved: {object_name} ({len(file_data)} bytes)")

            return file_data
        except S3Error as err:
            logger.error(f"Failed to retrieve file: {object_name}")
            raise StorageDownloadError(
                f"Не удалось получить файл '{object_name}' из хранилища."
            ) from err

    def delete_file(self, object_name: str) -> None:
        """Удаляет объект из MinIO."""
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )
            logger.info(f"File deleted: {object_name}")
        except S3Error as err:
            logger.error(f"Failed to delete file: {object_name}")
            raise StorageDeleteError(
                f"Не удалось удалить файл '{object_name}' из хранилища."
            ) from err
