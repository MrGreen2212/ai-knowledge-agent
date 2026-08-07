import io
import logging

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Сервис извлечения текста из документов (PDF, DOCX)."""

    def extract(self, file_data: bytes, filename: str) -> str:
        """Извлекает текст из файла."""
        ext = filename.split(".")[-1].lower()

        if ext == "pdf":
            return self._extract_pdf(file_data)

        if ext == "docx":
            return self._extract_docx(file_data)

        logger.warning(f"Unsupported file format: {ext}")
        return ""

    def _extract_pdf(self, file_data: bytes) -> str:
        """Извлекает текст из PDF."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_data))
            text = ""

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            logger.debug(f"Extracted {len(text)} characters from PDF")
            return text.strip()

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def _extract_docx(self, file_data: bytes) -> str:
        """Извлекает текст из DOCX."""
        try:
            import docx2txt

            process = getattr(docx2txt, "process", None)

            if process:
                text = process(io.BytesIO(file_data))
                logger.debug(f"Extracted {len(text)} characters from DOCX")
                return text

        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")

        return ""
