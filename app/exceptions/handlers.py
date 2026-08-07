from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.document import (
    DocumentNotFound,
    DocumentProcessingError,
)
from app.exceptions.storage import (
    FileDownloadError,
    FileUploadError,
)


async def upload_error_handler(
    request: Request,
    exc: FileUploadError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
        },
    )


async def download_error_handler(
    request: Request,
    exc: FileDownloadError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
        },
    )


async def document_not_found_handler(
    request: Request,
    exc: DocumentNotFound,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": str(exc),
        },
    )


async def document_processing_handler(
    request: Request,
    exc: DocumentProcessingError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрация глобальных обработчиков исключений."""

    app.add_exception_handler(
        FileUploadError,
        upload_error_handler, # type: ignore
    )

    app.add_exception_handler(
        FileDownloadError,
        download_error_handler, # type: ignore
    )

    app.add_exception_handler(
        DocumentNotFound,
        document_not_found_handler, # type: ignore
    )

    app.add_exception_handler(
        DocumentProcessingError,
        document_processing_handler, # type: ignore
    )