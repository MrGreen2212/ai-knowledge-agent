from typing import List, Optional, Dict, Any, Sequence

import chromadb


class VectorDatabaseService:
    """Сервис для работы с векторной базой данных."""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=".chroma")

    # Логика проверки существования коллекции должна быть в самом начале метода,
    # а не внутри комментария-указаний для статического анализатора.
    def create_collection(self) -> None:
        """
        Создаёт новую коллекцию документов или сообщает о её наличии.
        
        Args: нет
        Returns: ничего (None)
        """
        name = "knowledge_base"
    
        if name in self.client.list_collections():
            print(f"Коллекция {name} уже существует.")
            return  # <-- Это ключевая строка! Она предотвращает повторное создание.

        # Подавляем ошибки типа для методов библиотеки ChromaDB,
        # так как она не имеет строгих типов (*stubs*).
        collection = self.client.create_collection(  
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        embeddings: Sequence[Sequence[float]],
        ids: Sequence[str],  
        metadatas: Optional[Sequence[Dict[str, Any]]] = None 
    ) -> None:
        """
        Добавляет документы в существующую коллекцию.
        
        Args:
            embeddings: Список списков чисел (вектора).
            ids: Список уникальных ID каждого чанка текста.
            metadatas: Опционально, метаданные.
        """

        collection = self.client.get_collection("knowledge_base")  # type: ignore[reportGeneralTypeIssues]

        assert len(embeddings) == len(ids), "Длина векторов и id должна совпадать."

        # Если метаданные не переданы, создаем пустые словари
        if not metadatas:
            metadatas = [{}] * len(embeddings)

        collection.add(
            embeddings=embeddings,
            documents=None,
            ids=ids,
            metadatas=metadatas
        )

    # Подавление проблем с опциональными объектами и неизвестными аргументами
    def query(
        self,
        embedding: list[float],
        limit: int = 5
    ):
        """
        Ищет наиболее релевантные документы по вектору запроса.
        
        Args:
            embedding: Вектор запроса.
            limit: Количество результатов.
            
        Returns:
            Список кортежей (id_чанка, степень схожести).
        """

        try:
            collection = self.client.get_collection("knowledge_base")  # type: ignore[reportOptionalSubscript]
        except Exception as e:
            print(f"Векторная база данных недоступна: {e}")
            return []

        results = collection.query(query_embeddings=[embedding], n_results=limit)  # type: ignore[reportUnknownArgumentType]

        distances = results.get("distances", [])
        ids = results.get("ids", [])

        # Проверка на случай пустой коллекции или отсутствия результатов
        return list(zip(ids[0], distances[0])) if ids and distances else []