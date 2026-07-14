import uuid
from io import BytesIO
from typing import Any, Dict, IO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


# Инициализация клиента остается глобальной для переиспользования соединения
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


class StorageService:
    def __init__(self) -> None:  # <-- Явный тип возврата для конструктора
        self.client: Minio = client
        self.bucket_name: str = settings.MINIO_BUCKET
        
        # Создаем бакет сразу при создании экземпляра сервиса
        create_bucket()

    def upload_file(
        self, 
        file_data: bytes, 
        original_filename: str, 
        content_type: str
    ) -> Dict[str, Any]:
        """
        Загружает бинарные данные в MinIO.
        """
        ext = original_filename.split('.')[-1]
        object_name = f"{uuid.uuid4()}.{ext}"

        try:
            file_stream = BytesIO(file_data)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type
            )
            
            return {
                "status": "success",
                "bucket": self.bucket_name,
                "object_name": object_name,
                "original_filename": original_filename,
                "size": len(file_data)
            }
        except S3Error as err:
            print(f"Ошибка при загрузке в MinIO: {err}")
            raise

    def get_file(self, object_name: str) -> bytes:
        """
        Скачивает объект из MinIO и возвращает его содержимое как байты.
        """
        try:
            response: IO[bytes] = self.client.get_object(  # type: ignore
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            file_data: bytes = response.read()
            response.close()
            
            return file_data
        except S3Error as err:
            print(f"Ошибка при чтении из MinIO: {err}")
            raise