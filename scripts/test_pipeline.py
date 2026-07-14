from app.services.rag_service import RAGService

# Имя файла должно быть точным именем объекта в MinIO (без лишних параметров)
OBJECT_NAME = "9047339c-0557-45f8-a7d8-a81ff3aa7442.pdf"

def main():
    # Создаём единый сервис, который управляет всем пайплайном
    rag = RAGService()

    print("Инициализируем векторную базу...")
    # Если коллекция уже существует, она будет просто использована
    rag.vector_db.create_collection()

    # Индексировать документ только при необходимости
    INDEX_DOCUMENT = False

    if INDEX_DOCUMENT:

        try:
            # Полная индексация документа: загрузка → текст → эмбеддинги → сохранение
            print(f"\n🔥 Индексация документа {OBJECT_NAME}...")
            rag.process_document(OBJECT_NAME)  # <-- Всё происходит здесь!
        except Exception as e:
            print(f"Ошибка при индексировании: {e}")
    
    while True:
        query = input("\nВведите вопрос ('exit' для выхода): ")
        
        if query.lower().strip() == "exit":
            break

        results = rag.search(query=query)

        # Выводим результаты поиска по смыслу запроса
        for result in results:
            print("=" * 80)
            print(f"Score: {result['score']:.4f}")
            print(result["text"][:800])

if __name__ == "__main__":
    main()