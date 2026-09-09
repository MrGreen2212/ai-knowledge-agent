from app.core.dependencies import get_rag_service

OBJECT_NAME = "9047339c-0557-45f8-a7d8-a81ff3aa7442.pdf"
DOCUMENT_ID = "document-id-for-test"


def main():

    rag = get_rag_service()

    print("Инициализируем векторную базу...")
    
    INDEX_DOCUMENT = False

    if INDEX_DOCUMENT:
        print(f"\n🔥 Индексация документа {OBJECT_NAME}...")
        rag.process_document(
            object_name=OBJECT_NAME,
            document_id=DOCUMENT_ID,
        )

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