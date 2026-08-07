"""
Абстрактный интерфейс для Storage провайдеров.

Определяет контракт для всех реализаций файловых хранилищ.
Следует принципу Dependency Inversion Principle (DIP) из SOLID.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class StorageProvider(ABC):
    """
    Абстрактный базовый класс для Storage провайдеров.
    
    Определяет минимальный контракт для работы с файловыми хранилищами.
    Любая реализация (MinIO, S3, Azure Blob, etc.) должна реализовать этот интерфейс.
    
    Принципы:
    - Interface Segregation Principle: минимальный необходимый интерфейс
    - Dependency Inversion Principle: зависимость от абстракции, а не от конкретной реализации
    - Open/Closed Principle: открыт для расширения (новые провайдеры), закрыт для модификации
    """
    
    @abstractmethod
    def upload_file(
        self,
        file_data: bytes,
        original_filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """
        Загружает файл в хранилище.
        
        Args:
            file_data: Содержимое файла в байтах
            original_filename: Оригинальное имя файла
            content_type: MIME-тип файла
            
        Returns:
            Словарь с информацией о загруженном файле:
            - status: статус операции
            - bucket: название бакета/контейнера
            - object_name: имя объекта в хранилище
            - original_filename: оригинальное имя файла
            - size: размер файла в байтах
            
        Raises:
            FileUploadError: Если произошла ошибка при загрузке файла
        """
        pass
    
    @abstractmethod
    def get_file(self, object_name: str) -> bytes:
        """
        Скачивает файл из хранилища.
        
        Args:
            object_name: Имя объекта в хранилище
            
        Returns:
            Содержимое файла в байтах
            
        Raises:
            FileDownloadError: Если произошла ошибка при скачивании файла
        """
        pass
