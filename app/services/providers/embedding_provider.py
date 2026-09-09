"""
Абстрактный интерфейс для Embedding провайдеров.

Определяет контракт для всех реализаций создания эмбеддингов.
Следует принципу Dependency Inversion Principle (DIP) из SOLID.
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Абстрактный базовый класс для Embedding провайдеров.

    Определяет минимальный контракт для создания векторных представлений текста.
    Любая реализация (SentenceTransformers, OpenAI, Cohere, etc.) должна реализовать этот интерфейс.

    Принципы:
    - Interface Segregation Principle: минимальный необходимый интерфейс
    - Dependency Inversion Principle: зависимость от абстракции, а не от конкретной реализации
    - Open/Closed Principle: открыт для расширения (новые провайдеры), закрыт для модификации
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создает эмбеддинги для списка текстов.

        Args:
            texts: Список текстов для создания эмбеддингов

        Returns:
            Список векторов (эмбеддингов) для каждого текста

        Raises:
            EmbeddingProviderError: Если произошла ошибка при создании эмбеддингов
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Создает эмбеддинг для одного текста (запроса).

        Args:
            text: Текст для создания эмбеддинга

        Returns:
            Вектор (эмбеддинг) текста

        Raises:
            EmbeddingProviderError: Если произошла ошибка при создании эмбеддинга
        """
        pass
