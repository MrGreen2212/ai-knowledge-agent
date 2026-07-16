from sqlalchemy.orm import Session

from app.services.document_service import DocumentService
from app.services.rag_service import RAGService


class DocumentWorkflowService:
    """
    Оркестратор процесса загрузки документа.

    Отвечает за полный жизненный цикл:
        upload →
        save metadata →
        index →
        return result
    """

    def __init__(
        self,
        document_service: DocumentService,
        rag_service: RAGService,
    ):
        self.document_service = document_service
        self.rag_service = rag_service