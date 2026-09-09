import logging
from typing import Any, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.providers.chroma_provider import ChromaProvider

logger = logging.getLogger(__name__)


class DocumentWorkflowService:
    """Оркестратор процесса загрузки документа."""

    def __init__(
        self,
        document_service: DocumentService,
        rag_service: RAGService,
        chroma_provider: ChromaProvider | None = None,
    ):
        self.document_service = document_service
        self.rag_service = rag_service
        self.chroma_provider = chroma_provider or ChromaProvider()

    def upload_document(
        self,
        db: Session,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        logger.info(f"Starting document workflow for file: {filename}")

        document = self.document_service.create_document(
            db=db,
            file_data=file_data,
            filename=filename,
            content_type=content_type,
        )

        logger.info(f"Document saved: {document['object_name']}")

        self.rag_service.process_document(
            object_name=document["object_name"],
            document_id=document["id"],
        )

        logger.info(f"Document indexed successfully: {document['object_name']}")

        return document

    def list_documents(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
    ):
        """Возвращает список документов."""
        return self.document_service.list_documents(
            db=db,
            limit=limit,
            offset=offset,
        )
    def get_document(
        self,
        db: Session,
        document_id: UUID,
    ):
        """Возвращает документ по ID."""
        return self.document_service.get_document(
            db=db,
            document_id=document_id,
        )

    def delete_document(
        self,
        db: Session,
        document_id: UUID,
    ) -> bool:
        """Удаляет документ из Chroma, MinIO и PostgreSQL."""
        document = self.document_service.get_document(
            db=db,
            document_id=document_id,
        )
        if document is None:
            return False

        chunk_ids = self.chroma_provider.get_chunk_ids_by_document_id(document_id)
        self.chroma_provider.delete_documents(chunk_ids)
        self.document_service.storage.delete_file(document.object_name)

        deleted = self.document_service.repository.delete(
            db=db,
            document_id=document_id,
        )
        if not deleted:
            raise RuntimeError(f"Document disappeared during deletion: {document_id}")

        logger.info(f"Document deleted: {document_id}")
        return True