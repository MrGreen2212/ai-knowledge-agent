import logging
from typing import Any, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.providers import StorageProvider

logger = logging.getLogger(__name__)


class DocumentService:
    """Сервис для работы с документами (Storage + PostgreSQL)."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: StorageProvider,
    ):
        self.repository = repository
        self.storage = storage

    def create_document(
        self,
        db: Session,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """Сохраняет документ в MinIO и метаданные в PostgreSQL."""
        logger.info(f"Creating document: {filename}")

        storage_result = self.storage.upload_file(
            file_data=file_data,
            original_filename=filename,
            content_type=content_type,
        )

        logger.debug(f"File uploaded to storage: {storage_result['object_name']}")

        document_in_db = self.repository.create(
            db=db,
            filename=storage_result["original_filename"],
            object_name=storage_result["object_name"],
            content_type=content_type,
            size=storage_result["size"],
        )

        logger.info(f"Document metadata saved to database: {document_in_db.id}")

        return {
            "id": document_in_db.id,
            "filename": document_in_db.filename,
            "object_name": document_in_db.object_name,
            "status": "uploaded",
            "size": document_in_db.size,
        }

    def list_documents(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        ):
        """Возвращает список документов из PostgreSQL."""
        return self.repository.list(
            db=db,
            limit=limit,
            offset=offset,
        )
    def get_document(
        self,
        db: Session,
        document_id: UUID,
    ):
        """Возвращает документ по ID из PostgreSQL."""
        return self.repository.get_by_id(
            db=db,
            document_id=document_id,
        )