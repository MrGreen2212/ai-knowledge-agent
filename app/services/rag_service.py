import json
from typing import List, Dict, Optional

# Импортируем наши сервисы
from .storage import StorageService
from .embedding_service import EmbeddingService
from .vector_db import VectorDatabaseService
from .document_service import DocumentService


class RAGService:
    """
    Полный RAG pipeline.

    upload ->
    extract ->
    chunk ->
    embed ->
    save vectors ->
    search
    """

    CHUNK_SIZE = 500

    def __init__(self):
        self.storage = StorageService()
        self.embedding = EmbeddingService()
        self.vector_db = VectorDatabaseService()
        self.document_service = DocumentService()

    def process_document(
        self,
        object_name: str,
    ) -> None:
        """
        Полностью индексирует документ.

        Args:
            object_name: Имя объекта в MinIO (например, "fa312b38-d1ad-4606-9657-c54d490c64a3.pdf").
        Raises:
            ValueError: если не удалось извлечь текст.
        """

        file_data = self.storage.get_file(object_name)

        text = self.document_service._extract_text(file_data=file_data, filename=object_name)

        if not text.strip():
            raise ValueError("Не удалось извлечь текст из документа.")

        chunks = self._split_text(text)

        embeddings = self.embedding.embed_documents(chunks)

        document_id = object_name.split(".")[0]

        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        # Мы храним только служебную информацию в метаданных
        metadatas = [{
            "document_id": document_id,
            "object_name": object_name,
            "chunk_index": i,
        } for i in range(len(chunks))]

        # Тексты чанков сохраняются в стандартное поле documents базы данных
        self.vector_db.add_documents(
            texts=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    def search(
        self,
        query: str,
        limit: int = 3
    ):

        vector = self.embedding.embed_query(query)

        return self.vector_db.query(
            embedding=vector,
            limit=limit
    )

    def _split_text(
        self,
        text: str
    ) -> List[str]:
        """
        Разбивает большой текст на фрагменты фиксированного размера (~CHUNK_SIZE слов).

        Args:
            text: Исходный текст документа.

        Returns:
            Список строк — отдельные фрагменты.
        """
        chunks = []
        current_chunk = ""

        for sentence in text.split("\n"):
            words_in_current = len(current_chunk.split())

            # Если текущий чанк ещё мал или пустой
            if words_in_current < self.CHUNK_SIZE or current_chunk == "":
                current_chunk += "\n" + sentence
            else:
                # Иначе добавляем завершённый чанк и начинаем новый
                chunks.append(current_chunk.strip())
                current_chunk = sentence

        # Не забываем добавить последний незавершённый чанк
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks