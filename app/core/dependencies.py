from app.repositories.document_repository import DocumentRepository

from app.services.document_service import DocumentService
from app.services.document_workflow_service import DocumentWorkflowService
from app.services.embedding_service import EmbeddingService
from app.services.ollama_service import OllamaService
from app.services.rag_service import RAGService
from app.services.storage import StorageService
from app.services.text_extraction_service import TextExtractionService
from app.services.vector_db import VectorDatabaseService


def get_document_service() -> DocumentService:

    repository = DocumentRepository()
    storage = StorageService()
    
    return DocumentService(
        repository=repository,
        storage=storage,
    )


def get_rag_service() -> RAGService:

    storage = StorageService()

    extractor = TextExtractionService()

    embedding = EmbeddingService()

    vector_db = VectorDatabaseService()

    return RAGService(
        storage=storage,
        extractor=extractor,
        embedding=embedding,
        vector_db=vector_db,
    )


def get_document_workflow_service() -> DocumentWorkflowService:

    return DocumentWorkflowService(
        document_service=get_document_service(),
        rag_service=get_rag_service(),
    )


def get_ollama_service() -> OllamaService:
    """Создает экземпляр OllamaService."""
    return OllamaService()
