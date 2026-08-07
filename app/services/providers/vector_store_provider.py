"""
Абстрактный интерфейс для Vector Store провайдеров.

Определяет контракт для всех реализаций векторных баз данных.
Следует принципу Dependency Inversion Principle (DIP) из SOLID.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Sequence, Optional


class VectorStoreProvider(ABC):
    """
    Абстрактный базовый класс для Vector Store провайдеров.
    
    Определяет минимальный контракт для работы с векторными базами данных.
    Любая реализация (Chroma, Pinecone, Weaviate, etc.) должна реализовать этот интерфейс.
    
    Принципы:
    - Interface Segregation Principle: минимальный необходимый интерфейс
    - Dependency Inversion Principle: зависимость от абстракции, а не от конкретной реализации
    - Open/Closed Principle: открыт для расширения (новые провайдеры), закрыт для модификации
    """
    
    @abstractmethod
    def add_documents(
        self,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        """
        Добавляет документы в векторное хранилище.
        
        Args:
            texts: Список текстов документов
            embeddings: Список векторных представлений
            ids: Список уникальных идентификаторов
            metadatas: Список метаданных для каждого документа (опционально)
            
        Raises:
            VectorStoreProviderError: Если произошла ошибка при добавлении документов
        """
        pass
    
    @abstractmethod
    def query(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Выполняет поиск по векторному представлению.
        
        Args:
            embedding: Векторное представление запроса
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных документов с метаданными и оценками релевантности
            Каждый элемент должен содержать:
            - id: уникальный идентификатор
            - score: оценка релевантности
            - text: текст документа
            - metadata: метаданные документа
            
        Raises:
            VectorStoreProviderError: Если произошла ошибка при поиске
        """
        pass
