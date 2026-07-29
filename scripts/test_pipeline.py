from app.core.dependencies import get_rag_service

OBJECT_NAME = "9047339c-0557-45f8-a7d8-a81ff3aa7442.pdf"


def main():

    rag = get_rag_service()

    print("Инициализируем векторную базу...")
    rag.vector_db.create_collection()
    print(rag.vector_db.client.list_collections())

    INDEX_DOCUMENT = False

    if INDEX_DOCUMENT:
        print(f"\n🔥 Индексация документа {OBJECT_NAME}...")
        rag.process_document(OBJECT_NAME)

    while True:

        query = input("\nВведите вопрос ('exit' для выхода): ")

        if query.lower() == "exit":
            break

        results = rag.search(query)

        for i, result in enumerate(results):
            print("-" * 80)
            print(f"{i + 1}. Схожесть: {result['score']:.4f}")
            print(result["text"])
            print(result["metadata"]["object_name"])

if __name__ == "__main__":
    main()