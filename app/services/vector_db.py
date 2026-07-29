import logging
from typing import List, Optional, Dict, Any, Sequence

import chromadb

logger = logging.getLogger(__name__)


class VectorDatabaseService:
    """Сервис для работы с векторной базой данных ChromaDB."""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=".chroma")
        self.collection_name = "knowledge_base"
        self._ensure_collection()

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
        """Добавляет документы в коллекцию."""
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

    def query(self, embedding: list[float], limit: int = 5) -> list[dict]:
        """Выполняет поиск по векторному представлению."""
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
