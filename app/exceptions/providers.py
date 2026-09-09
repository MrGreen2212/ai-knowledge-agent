"""
Исключения для провайдеров.

Унифицированная система исключений для всех провайдеров (LLM, Embedding, Vector Store, Storage).
"""


class ProviderError(Exception):
    """Базовое исключение для всех провайдеров."""

    pass


# LLM Provider Exceptions
class LLMProviderError(ProviderError):
    """Базовое исключение для LLM провайдеров."""

    pass


class LLMGenerationError(LLMProviderError):
    """Ошибка при генерации текста через LLM."""

    pass


class LLMConnectionError(LLMProviderError):
    """Ошибка подключения к LLM сервису."""

    pass


class LLMTimeoutError(LLMProviderError):
    """Превышено время ожидания ответа от LLM."""

    pass


# Embedding Provider Exceptions
class EmbeddingProviderError(ProviderError):
    """Базовое исключение для Embedding провайдеров."""

    pass


class EmbeddingGenerationError(EmbeddingProviderError):
    """Ошибка при создании эмбеддингов."""

    pass


class EmbeddingModelLoadError(EmbeddingProviderError):
    """Ошибка при загрузке модели эмбеддингов."""

    pass


# Vector Store Provider Exceptions
class VectorStoreProviderError(ProviderError):
    """Базовое исключение для Vector Store провайдеров."""

    pass


class VectorStoreConnectionError(VectorStoreProviderError):
    """Ошибка подключения к векторной базе данных."""

    pass


class VectorStoreQueryError(VectorStoreProviderError):
    """Ошибка при поиске в векторной базе данных."""

    pass


class VectorStoreInsertError(VectorStoreProviderError):
    """Ошибка при добавлении документов в векторную базу данных."""

    pass


# Storage Provider Exceptions
class StorageProviderError(ProviderError):
    """Базовое исключение для Storage провайдеров."""

    pass


class StorageConnectionError(StorageProviderError):
    """Ошибка подключения к хранилищу."""

    pass


class StorageUploadError(StorageProviderError):
    """Ошибка при загрузке файла в хранилище."""

    pass


class StorageDownloadError(StorageProviderError):
    """Ошибка при скачивании файла из хранилища."""

    pass


class StorageDeleteError(StorageProviderError):
    """Ошибка при удалении файла из хранилища."""

    pass
