"""
Chroma реализация VectorStoreProvider.

Конкретная реализация интерфейса VectorStoreProvider для работы с ChromaDB.
"""

import logging
from typing import List, Dict, Any, Sequence, Optional

import chromadb

from app.exceptions.providers import VectorStoreConnectionError, VectorStoreInsertError, VectorStoreQueryError
from .vector_store_provider import VectorStoreProvider

logger = logging.getLogger(__name__)


class ChromaProvider(VectorStoreProvider):
    """
    Chroma реализация VectorStoreProvider.
    
    Использует ChromaDB для хранения и поиска векторных представлений документов.
    Реализует интерфейс VectorStoreProvider, следуя принципу Liskov Substitution Principle (LSP).
    """

    def __init__(self, path: str = ".chroma", collection_name: str = "knowledge_base"):
        """
        Инициализирует Chroma провайдер.
        
        Args:
            path: Путь к директории для хранения данных ChromaDB
            collection_name: Название коллекции
            
        Raises:
            VectorStoreConnectionError: Если не удалось инициализировать ChromaDB
        """
        try:
            self.client = chromadb.PersistentClient(path=path)
            self.collection_name = collection_name
            self._ensure_collection()
            logger.info(f"ChromaProvider initialized with collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise VectorStoreConnectionError(f"Не удалось инициализировать ChromaDB: {e}")

    def _ensure_collection(self) -> None:
        """Создает или получает существующую коллекцию."""
        if self.collection_name in [c.name for c in self.client.list_collections()]:
            logger.info(f"Collection already exists: {self.collection_name}")
        else:
            logger.info(f"Creating collection: {self.collection_name}")

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        """
        Добавляет документы в ChromaDB коллекцию.
        
        Args:
            texts: Список текстов документов
            embeddings: Список векторных представлений
            ids: Список уникальных идентификаторов
            metadatas: Список метаданных для каждого документа (опционально)
            
        Raises:
            VectorStoreInsertError: Если произошла ошибка при добавлении документов
        """
        try:
            assert len(embeddings) == len(ids), (
                f"Длина векторов ({len(embeddings)}) "
                f"и id ({len(ids)}) должны совпадать."
            )
            assert len(texts) == len(ids), (
                f"Количество текстов ({len(texts)}) "
                f"должно совпадать с количеством ID ({len(ids)})."
            )

            if not metadatas:
                metadatas = [{}] * len(embeddings)

            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
            )

            logger.info(f"Added {len(ids)} documents to collection")
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise VectorStoreInsertError(f"Ошибка при добавлении документов в ChromaDB: {e}")

    def query(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Выполняет поиск по векторному представлению в ChromaDB.
        
        Args:
            embedding: Векторное представление запроса
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных документов с метаданными и оценками релевантности
            
        Raises:
            VectorStoreQueryError: Если произошла ошибка при поиске
        """
        try:
            raw = self.collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                include=["documents", "distances", "metadatas"],
            )

            results = []
            ids = raw["ids"][0]
            docs = raw["documents"][0]
            distances = raw["distances"][0]
            metas = raw["metadatas"][0]

            for i in range(len(ids)):
                results.append(
                    {
                        "id": ids[i],
                        "score": float(distances[i]),
                        "text": docs[i],
                        "metadata": metas[i],
                    }
                )

            logger.debug(f"Query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            raise VectorStoreQueryError(f"Ошибка при поиске в ChromaDB: {e}")
