from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_document_workflow_service
from app.services.document_workflow_service import DocumentWorkflowService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    workflow: DocumentWorkflowService = Depends(get_document_workflow_service),
):
    """Загружает документ и индексирует его в векторную базу данных."""
    file_data = await file.read()
    filename = file.filename or "unknown_file"
    content_type = file.content_type or "application/octet-stream"

    return workflow.upload_document(
        db=db,
        file_data=file_data,
        filename=filename,
        content_type=content_type,
    )
