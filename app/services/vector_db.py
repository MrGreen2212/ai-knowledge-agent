from typing import List, Optional, Dict, Any, Sequence

import chromadb


class VectorDatabaseService:
    """Сервис для работы с векторной базой данных."""

    def __init__(self):
        # Локальное хранилище ChromaDB в папке .chroma/
        self.client = chromadb.PersistentClient(path=".chroma")

    def create_collection(self) -> None:
        """
        Создаёт или получает существующую коллекцию документов.
        
        Args: нет
        Returns: ничего (None)

        Notes:
            - Указываем пространство расстояний "cosine" как оптимальное для текстов.
            - Параметр get_or_create=True гарантирует корректное поведение при повторном запуске.
              Если коллекция уже существует, она будет использована с текущими параметрами.
            - embedding_function=None говорит ChromaDB, что мы будем передавать готовые вектора,
              а не использовать встроенные модели.
        """
        collection_name = "knowledge_base"
    
        if collection_name in [c.name for c in self.client.list_collections()]:
            print(f"Коллекция {collection_name} уже существует.")

        # type: ignore[reportGeneralTypeIssues]
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            get_or_create=True,
            embedding_function=None
        )

    # Подавляем ошибки типа для методов библиотеки ChromaDB
    # type: ignore[reportGeneralTypeIssues]
    def add_documents(
        self,
        texts: Sequence[str],          # Текстовые фрагменты идут сюда
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],  
        metadatas: Optional[Sequence[Dict[str, Any]]] = None 
    ) -> None:
        """
        Добавляет документы в существующую коллекцию.
        
        Args:
            texts: Списки строк — тексты чанков.
            embeddings: Список списков чисел (вектора).
            ids: Список уникальных ID каждого чанка текста.
            metadatas: Опционально, метаданные.
            
        Проверки:
            Длина всех массивов должна совпадать!
        """

        assert len(embeddings) == len(ids), (
            f"Длина векторов ({len(embeddings)}) "
            f"и id ({len(ids)}) должны совпадать."
        )
        assert len(texts) == len(ids), (
            f"Количество текстов ({len(texts)}) "
            f"должно совпадать с количеством ID ({len(ids)})."
        )

        # Если метаданные не переданы, создаем пустые словари
        if not metadatas:
            metadatas = [{}] * len(embeddings)

        # Сохраняем тексты в стандартное поле documents
        collection = self.client.get_collection("knowledge_base")  
        collection.add(  
            documents=texts,      # <-- Передаём тексты напрямую
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    # Подавляем проблемы с опциональными объектами при поиске
    # type: ignore[reportOptionalSubscript]
    def query(
        self,
        embedding: list[float],
        limit: int = 5
    ) -> list[dict]:

        collection = self.client.get_collection("knowledge_base")
        print(f"Всего документов в Chroma: {collection.count()}")

        raw = collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            include=["documents", "distances", "metadatas"]
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
                    "metadata": metas[i]
                }
            )

        return results