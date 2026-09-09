from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.document_workflow_service import DocumentWorkflowService
from app.services.providers import (
    ChromaProvider,
    EmbeddingProvider,
    FastEmbedProvider,
    LLMProvider,
    MinIOProvider,
    OllamaProvider,
    StorageProvider,
    VectorStoreProvider,
)
from app.services.rag_service import RAGService
from app.services.text_extraction_service import TextExtractionService


def get_llm_provider() -> LLMProvider:
    """
    Создает экземпляр LLM провайдера.

    Returns:
        LLMProvider: Конкретная реализация LLM провайдера (OllamaProvider)
    """
    return OllamaProvider()


def get_embedding_provider() -> EmbeddingProvider:
    """
    Создает экземпляр Embedding провайдера.

    Returns:
        EmbeddingProvider: Конкретная реализация Embedding провайдера (FastEmbedProvider)
    """
    return FastEmbedProvider()


def get_vector_store_provider() -> VectorStoreProvider:
    """
    Создает экземпляр Vector Store провайдера.

    Returns:
        VectorStoreProvider: Конкретная реализация Vector Store провайдера (ChromaProvider)
    """
    return ChromaProvider()


def get_storage_provider() -> StorageProvider:
    """
    Создает экземпляр Storage провайдера.

    Returns:
        StorageProvider: Конкретная реализация Storage провайдера (MinIOProvider)
    """
    return MinIOProvider()


def get_document_service() -> DocumentService:

    repository = DocumentRepository()
    storage = get_storage_provider()

    return DocumentService(
        repository=repository,
        storage=storage,
    )


def get_rag_service() -> RAGService:
    """
    Создает экземпляр RAGService с зависимостями.

    Использует Dependency Injection для внедрения всех зависимостей,
    включая LLM, Embedding, Vector Store и Storage провайдеры.
    """
    storage = get_storage_provider()
    extractor = TextExtractionService()
    embedding = get_embedding_provider()
    vector_store = get_vector_store_provider()
    llm = get_llm_provider()

    return RAGService(
        storage=storage,
        extractor=extractor,
        embedding=embedding,
        vector_store=vector_store,
        llm=llm,
    )


def get_document_workflow_service() -> DocumentWorkflowService:

    return DocumentWorkflowService(
        document_service=get_document_service(),
        rag_service=get_rag_service(),
        chroma_provider=get_vector_store_provider(),
    )


def get_conversation_service() -> ConversationService:
    """Создает экземпляр ConversationService."""
    conversation_repository = ConversationRepository()
    message_repository = MessageRepository()

    return ConversationService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
    )
