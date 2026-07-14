from fastapi import APIRouter, File, UploadFile, status, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_data = await file.read()

    service = DocumentService()

    filename = file.filename or "unknown_file"
    content_type = file.content_type or "application/octet-stream"

    return service.create_document(
        db=db,
        file_data=file_data,
        filename=filename,
        content_type=content_type
    )