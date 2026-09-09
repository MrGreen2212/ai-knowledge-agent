"""
FastEmbed реализация EmbeddingProvider.

Конкретная реализация интерфейса EmbeddingProvider для работы с FastEmbed.
"""

import logging
from typing import List

from fastembed import TextEmbedding as TextEmbeddingModel

from app.exceptions.providers import EmbeddingGenerationError, EmbeddingModelLoadError

from .embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class FastEmbedProvider(EmbeddingProvider):
    """
    FastEmbed реализация EmbeddingProvider.

    Использует FastEmbed с моделью sentence-transformers/all-MiniLM-L6-v2
    для создания векторных представлений текста.
    Реализует интерфейс EmbeddingProvider, следуя принципу Liskov Substitution Principle (LSP).
    """

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"
    ):
        """
        Инициализирует FastEmbed провайдер.

        Args:
            model_name: Название модели для создания эмбеддингов
            device: Устройство для вычислений ('cpu' или 'cuda')

        Raises:
            EmbeddingModelLoadError: Если не удалось загрузить модель
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = TextEmbeddingModel(
                name=model_name,
                device=device,
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingModelLoadError(f"Не удалось загрузить модель эмбеддингов: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создает эмбеддинги для списка текстов.

        Args:
            texts: Список текстов для создания эмбеддингов

        Returns:
            Список векторов (эмбеддингов) для каждого текста

        Raises:
            EmbeddingGenerationError: Если произошла ошибка при создании эмбеддингов
        """
        try:
            embeddings = list(self.model.embed(texts))
            logger.debug(f"Generated embeddings for {len(texts)} texts")
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise EmbeddingGenerationError(f"Ошибка при создании эмбеддингов: {e}")

    def embed_query(self, text: str) -> List[float]:
        """
        Создает эмбеддинг для одного текста (запроса).

        Args:
            text: Текст для создания эмбеддинга

        Returns:
            Вектор (эмбеддинг) текста

        Raises:
            EmbeddingGenerationError: Если произошла ошибка при создании эмбеддинга
        """
        try:
            embedding_array = next(self.model.embed([text]))  # type: ignore[call-overload]
            return embedding_array.tolist()  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Failed to create query embedding: {e}")
            raise EmbeddingGenerationError(f"Ошибка при создании эмбеддинга запроса: {e}")
