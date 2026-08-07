import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.services.document_service import DocumentService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class DocumentWorkflowService:
    """Оркестратор процесса загрузки документа."""

    def __init__(
        self,
        document_service: DocumentService,
        rag_service: RAGService,
    ):
        self.document_service = document_service
        self.rag_service = rag_service

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

        self.rag_service.process_document(document["object_name"])

        logger.info(f"Document indexed successfully: {document['object_name']}")

        return document
