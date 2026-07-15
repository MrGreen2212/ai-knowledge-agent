import io


class TextExtractionService:
    """
    Сервис извлечения текста из различных форматов документов.
    """

    def extract(
        self,
        file_data: bytes,
        filename: str
    ) -> str:
        """
        Извлекает текст из файла.
        Поддерживаются PDF и DOCX.
        """

        ext = filename.split(".")[-1].lower()

        if ext == "pdf":
            return self._extract_pdf(file_data)

        if ext == "docx":
            return self._extract_docx(file_data)

        return ""

    def _extract_pdf(
        self,
        file_data: bytes
    ) -> str:

        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_data))

            text = ""

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

            return text.strip()

        except Exception:
            return ""

    def _extract_docx(
        self,
        file_data: bytes
    ) -> str:

        try:
            import docx2txt

            process = getattr(docx2txt, "process", None)

            if process:
                return process(io.BytesIO(file_data))

        except Exception:
            pass

        return ""