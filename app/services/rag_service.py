import logging
from typing import List, Dict, Any

from .text_extraction_service import TextExtractionService
from .storage import StorageService
from .embedding_service import EmbeddingService
from .vector_db import VectorDatabaseService

logger = logging.getLogger(__name__)


class RAGService:
    """Полный RAG pipeline для индексации и поиска документов."""

    CHUNK_SIZE = 500

    def __init__(
        self,
        storage: StorageService,
        extractor: TextExtractionService,
        embedding: EmbeddingService,
        vector_db: VectorDatabaseService,
    ):
        self.storage = storage
        self.extractor = extractor
        self.embedding = embedding
        self.vector_db = vector_db

    def process_document(self, object_name: str) -> None:
        """Индексирует документ в векторную базу данных."""
        logger.info(f"Processing document: {object_name}")

        file_data = self.storage.get_file(object_name)
        logger.debug(f"File retrieved from storage: {len(file_data)} bytes")

        text = self.extractor.extract(file_data=file_data, filename=object_name)

        if not text.strip():
            raise ValueError("Не удалось извлечь текст из документа.")

        chunks = self._split_text(text)
        logger.info(f"Document split into {len(chunks)} chunks")

        embeddings = self.embedding.embed_documents(chunks)
        logger.debug(f"Generated {len(embeddings)} embeddings")

        document_id = object_name.split(".")[0]
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "object_name": object_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        self.vector_db.add_documents(
            texts=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        logger.info(f"Document indexed successfully: {object_name}")
        
    def search(self, query: str, limit: int = 3):
        """Выполняет семантический поиск по документам."""
        logger.info(f"Searching for: {query}")

        vector = self.embedding.embed_query(query)

        results = self.vector_db.query(embedding=vector, limit=limit)

        logger.info(f"Found {len(results)} results")

        return results

    def _split_text(self, text: str) -> List[str]:
        """Разбивает текст на фрагменты фиксированного размера."""
        chunks = []
        current_chunk = ""

        for sentence in text.split("\n"):
            words_in_current = len(current_chunk.split())

            if words_in_current < self.CHUNK_SIZE or current_chunk == "":
                current_chunk += "\n" + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks