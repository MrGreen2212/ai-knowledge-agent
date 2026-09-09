"""
Chroma реализация VectorStoreProvider.

Конкретная реализация интерфейса VectorStoreProvider для работы с ChromaDB.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

import chromadb

from app.exceptions.providers import (
    VectorStoreConnectionError,
    VectorStoreInsertError,
    VectorStoreQueryError,
)

from .vector_store_provider import VectorStoreProvider

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "что",
    "такое",
    "это",
    "и",
    "в",
    "во",
    "на",
    "с",
    "со",
    "по",
    "из",
    "для",
    "как",
    "а",
    "но",
    "или",
}


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
                f"Длина векторов ({len(embeddings)}) " f"и id ({len(ids)}) должны совпадать."
            )
            assert len(texts) == len(ids), (
                f"Количество текстов ({len(texts)}) "
                f"должно совпадать с количеством ID ({len(ids)})."
            )

            if not metadatas:
                metadatas = [{}] * len(embeddings)

            self.collection.add(
                documents=list(texts),
                embeddings=list(embeddings),  # type: ignore[arg-type]
                ids=list(ids),
                metadatas=list(metadatas),  # type: ignore[arg-type]
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
                query_embeddings=[embedding],  # type: ignore[arg-type]
                n_results=limit,
                include=["documents", "distances", "metadatas"],
            )

            results = []
            # ChromaDB может вернуть None, но в нашем случае мы всегда запрашиваем эти поля
            ids = raw["ids"][0] if raw["ids"] else []
            docs = raw["documents"][0] if raw["documents"] else []
            distances = raw["distances"][0] if raw["distances"] else []
            metas = raw["metadatas"][0] if raw["metadatas"] else []

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

    def lexical_search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Ищет chunks по совпадениям нормализованных токенов в тексте.

        ``score`` — доля уникальных содержательных токенов запроса,
        найденных в chunk, в диапазоне от 0 до 1.
        """
        normalized_query = query.lower().replace("-", " ").replace("–", " ")
        token_pattern = re.compile(r"[а-яёa-z]+", re.IGNORECASE)
        query_tokens = list(
            dict.fromkeys(
                token
                for token in token_pattern.findall(normalized_query)
                if token not in STOP_WORDS
            )
        )

        if not query_tokens or limit <= 0:
            return []

        raw = self.collection.get(include=["documents", "metadatas"])
        ids = raw.get("ids") or []
        documents = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []
        results = []

        for chunk_id, document, metadata in zip(ids, documents, metadatas):
            normalized_document = (document or "").lower().replace("-", " ").replace("–", " ")
            document_tokens = token_pattern.findall(normalized_document)
            token_counts = {
                query_token: sum(
                    1
                    for document_token in document_tokens
                    if (
                        document_token == query_token
                        if len(query_token) < 5
                        else document_token.startswith(
                            query_token[: max(5, len(query_token) - 4)]
                        )
                    )
                )
                for query_token in query_tokens
            }
            matched_tokens = [
                query_token for query_token in query_tokens if token_counts[query_token] > 0
            ]

            if not matched_tokens:
                continue

            metadata = metadata or {}
            match_count = sum(token_counts.values())
            match_percentage = len(matched_tokens) / len(query_tokens)
            results.append(
                {
                    "id": chunk_id,
                    "score": match_percentage,
                    "text": document,
                    "metadata": {
                        **metadata,
                        "matched_tokens": matched_tokens,
                        "match_count": match_count,
                        "match_percentage": match_percentage,
                        "token_counts": token_counts,
                    },
                }
            )

        results.sort(
            key=lambda result: (
                -len(result["metadata"]["matched_tokens"]),
                -result["metadata"]["match_count"],
                result["metadata"].get("chunk_index", float("inf")),
            )
        )
        results = results[:limit]

        logger.info(
            "Lexical search returned %d results for query: %s",
            len(results),
            query,
        )
        return results

    def count(self) -> int:
        """Возвращает количество chunks в текущей коллекции без изменения данных."""
        return self.collection.count()

    def get_all_chunk_metadata(self) -> List[Dict[str, Any]]:
        """Возвращает metadata всех chunks без загрузки содержимого документов."""
        raw = self.collection.get(include=["metadatas"])
        return [metadata or {} for metadata in (raw.get("metadatas") or [])]

    def get_chunk_ids_by_document_id(self, document_id: UUID | str) -> List[str]:
        """Возвращает IDs chunks указанного документа без изменения Chroma."""
        raw = self.collection.get(
            where={"document_id": str(document_id)},
            include=["metadatas"],
        )
        return list(raw.get("ids") or [])

    def delete_documents(self, ids: Sequence[str]) -> None:
        """Удаляет chunks по явно переданным IDs."""
        if not ids:
            return

        try:
            self.collection.delete(ids=list(ids))
            logger.info(f"Deleted {len(ids)} chunks from collection")
        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {e}")
            raise VectorStoreInsertError(
                f"Ошибка при удалении документов из ChromaDB: {e}"
            )
