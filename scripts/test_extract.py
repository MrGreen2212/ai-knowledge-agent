import sys
from pypdf import PdfReader

def extract_text(file_path):
    try:
        reader = PdfReader(file_path)
        
        # Отладочные сообщения
        print(f"Найдено страниц: {len(reader.pages)}", file=sys.stderr)
        
        pages_texts = [page.extract_text().strip() for page in reader.pages]
        
        if not any(pages_texts):  # Если ни одна страница не вернула текст
            print("Ни одна страница не содержит распознанного текста.", file=sys.stderr)
            return ""

        return "\n\n".join([text for text in pages_texts if text])
    
    except ImportError as e:
        print("Библиотека PyPDF2/PyPDF не установлена:", str(e), file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    FILE_PATH = r"C:\Users\User\Documents\ai_knowledge_agent\data\uploads\fa312b38-d1ad-4606-9657-c54d490c64a3.pdf"
    extracted_text = extract_text(FILE_PATH)
    print(f"\nИзвлечено символов: {len(extracted_text)}")
    print("\nПервые 100 символов:")
    print(extracted_text[:100])