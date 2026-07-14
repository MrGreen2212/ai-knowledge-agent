import os
import io
import sys  # Для принудительного сброса буфера
from typing import List

# Импортируем наши сервисы
from app.services.storage import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.vector_db import VectorDatabaseService
from app.core.config import settings  # Для доступа к бакету

# Сервисы
storage = StorageService()
embedding_service = EmbeddingService()
vector_db_service = VectorDatabaseService()

# Шаг 0: Инициализация базы данных
print("Инициализируем векторную базу...")
vector_db_service.create_collection()  # Создаст папку .chroma/

# ---------------------------------------------------
# Шаг 1: Получение документа из MinIO
# ---------------------------------------------------

# Загрузите любой PDF-файл через Swagger UI по POST /documents/upload
# Посмотрите в БД PostgreSQL или DBeaver — найдите object_name этого файла.
OBJECT_NAME = "9047339c-0557-45f8-a7d8-a81ff3aa7442.pdf"  # <--- ЗАМЕНИТЕ НА РЕАЛЬНОЕ ИМЯ!
DOCUMENT_ID = OBJECT_NAME.split(".")[0]

try:
    file_data = storage.get_file(OBJECT_NAME)  # Получаем байты из MinIO
except Exception as e:
    print(f"Ошибка загрузки из MinIO: {e}")
    exit(1)

# ---------------------------------------------------
# ШАГ 2: Извлечение текста
# ---------------------------------------------------
def extract_text(file_data: bytes, filename: str) -> str:
    """Вспомогательная функция для извлечения текста."""
    ext = filename.split('.')[-1].lower()
    
    if ext == 'pdf':
        try:
            from pypdf import PdfReader
            
            print(f"Загружаем байты файла {filename}...", file=sys.stderr)
            reader = PdfReader(io.BytesIO(file_data))

            page_count = len(reader.pages)
            print(f"Найдено страниц: {page_count}", file=sys.stderr)

            pages_texts = [page.extract_text().strip() for page in reader.pages]

            # Проверяем, что хотя бы одна страница вернула текст
            if not any(pages_texts):
                print("Ни одна страница не содержит распознанного текста.", file=sys.stderr)

            return "\n\n".join([text for text in pages_texts if text])
        
        except ImportError as e:
            print("Библиотека PyPDF2/PyPDF не установлена:", str(e), file=sys.stderr)
            exit(1)

    elif ext == 'docx':  # На всякий случай оставляем поддержку docx
        try:
            import docx2txt
            return docx2txt.process(io.BytesIO(file_data))
        except ImportError:
            pass

    return ""

# Теперь вызываем эту функцию и сохраняем результат
text = extract_text(file_data, OBJECT_NAME)
if not text.strip():
    print("Не удалось извлечь текст из файла.")
    exit(1)

# Чанкинг
CHUNK_SIZE = 500  
chunks: List[str] = []
current_chunk = ""
for sentence in text.split("\n"):
    if len(current_chunk.split()) < CHUNK_SIZE - 100 or current_chunk == "":
        current_chunk += "\n" + sentence
    else:
        chunks.append(current_chunk.strip())
        current_chunk = sentence
if current_chunk:
    chunks.append(current_chunk.strip())

print(f"\nТекст документа разбит на {len(chunks)} чанков.")

# ---------------------------------------------------
# Шаг 3: Генерация эмбеддингов
# ---------------------------------------------------
embeddings = embedding_service.embed_documents(texts=chunks)
print(f"Сгенерировано {len(embeddings)} векторов размером {len(embeddings[0])}.")

# ---------------------------------------------------
# Шаг 4: Сохранение в базу данных
# ---------------------------------------------------
ids = [f"{DOCUMENT_ID}_chunk_{i}" for i in range(len(chunks))]
metadatas = [
    {"document_id": DOCUMENT_ID, "object_name": OBJECT_NAME, "chunk_index": i}
    for i in range(len(chunks))
]

vector_db_service.add_documents(
    embeddings=embeddings,
    ids=ids,
    metadatas=metadatas
)

print("\nЧанки успешно загружены в векторную базу!")

# ---------------------------------------------------
# Шаг 5: Тестовый поиск
# ---------------------------------------------------
query_text = input("\nЗадайте вопрос к документу: ")
query_embedding = embedding_service.embed_query(query_text)

results = vector_db_service.query(embedding=query_embedding, limit=3)

print("\nНайденные фрагменты:")
for chunk_id, score in results:
    print(f"- Чанк ID: {chunk_id}, Схожесть: {score:.4f}")