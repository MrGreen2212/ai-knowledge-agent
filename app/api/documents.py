from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_document_workflow_service
from app.schemas.document import DocumentResponse
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


@router.get(
    "",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить список документов",
    response_description="Список загруженных документов",
)
def list_documents(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    workflow: DocumentWorkflowService = Depends(get_document_workflow_service),
):
    """Возвращает список загруженных документов."""
    return workflow.list_documents(
        db=db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{document_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    workflow: DocumentWorkflowService = Depends(get_document_workflow_service),
):
    """Возвращает документ по ID."""
    document = workflow.get_document(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "object_name": document.object_name,
        "content_type": document.content_type,
        "size": document.size,
        "status": document.status,
        "created_at": document.created_at,
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить документ",
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    workflow: DocumentWorkflowService = Depends(get_document_workflow_service),
):
    """Удаляет документ из Chroma, MinIO и PostgreSQL."""
    deleted = workflow.delete_document(
        db=db,
        document_id=document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )