import io
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.storage import StorageService


class DocumentService:
    def __init__(self):
        self.repository = DocumentRepository()
        self.storage = StorageService()

    def _extract_text(self, file_data: bytes, filename: str) -> str:
        """
        Извлекает сырой текст из бинарных данных файла.
        Поддержка .docx и .pdf с защитой от отсутствия библиотек.
        """
        ext = filename.split('.')[-1].lower()
        text_result = ""

        if ext == 'docx':
            try:
                # Прячем импорт внутрь блока, чтобы избежать ошибок Stubs при анализе
                import docx2txt
                process_func = getattr(docx2txt, 'process', None)
                if process_func:
                    text_result = process_func(io.BytesIO(file_data))
            except ImportError:
                pass

        elif ext == 'pdf':
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_result += page_text + "\n"
                return text_result.strip()
            except ImportError:
                pass

        return text_result or ""

    def create_document(
        self,
        db: Session,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        
        storage_result = self.storage.upload_file(
            file_data=file_data,
            original_filename=filename,
            content_type=content_type
        )

        # Работа с ИИ временно закомментирована до настройки БД
        # extracted_text = self._extract_text(file_data, filename)
        # embedding_service = EmbeddingService()
        # vector = embedding_service.embed_documents([extracted_text])[0]

        document_in_db = self.repository.create(
            db=db,
            filename=storage_result["original_filename"],
            object_name=storage_result["object_name"],
            content_type=content_type,
            size=storage_result["size"]
        )

        return {
            "id": document_in_db.id,
            "filename": document_in_db.filename,
            "status": "uploaded",
            "size": document_in_db.size
        }