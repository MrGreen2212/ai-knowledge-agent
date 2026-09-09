class DocumentError(Exception):
    """Базовое исключение документов."""

    pass


class DocumentNotFound(DocumentError):
    """Документ не найден."""

    pass


class DocumentProcessingError(DocumentError):
    """Ошибка обработки документа."""

    pass
