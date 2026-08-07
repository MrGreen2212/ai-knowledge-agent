"""
Providers package - абстракции для внешних сервисов.

Содержит интерфейсы (абстрактные базовые классы) для различных провайдеров:
- LLMProvider: языковые модели
- EmbeddingProvider: модели эмбеддингов
- VectorStoreProvider: векторные базы данных
- StorageProvider: хранилища файлов

Следует принципам Clean Architecture и SOLID.
"""

from .llm_provider import LLMProvider
from .ollama_provider import OllamaProvider
from .embedding_provider import EmbeddingProvider
from .fastembed_provider import FastEmbedProvider
from .vector_store_provider import VectorStoreProvider
from .chroma_provider import ChromaProvider
from .storage_provider import StorageProvider
from .minio_provider import MinIOProvider

__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "EmbeddingProvider",
    "FastEmbedProvider",
    "VectorStoreProvider",
    "ChromaProvider",
    "StorageProvider",
    "MinIOProvider",
]
