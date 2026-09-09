class StorageError(Exception):
    """Базовое исключение для ошибок хранилища."""

    pass


class FileUploadError(StorageError):
    """Ошибка загрузки файла."""

    pass


class FileDownloadError(StorageError):
    """Ошибка скачивания файла."""

    pass
