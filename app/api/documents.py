from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
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
    """
    Загружает документ во временное хранилище (MinIO),
    сохраняет метаданные в PostgreSQL и возвращает ID документа.
    """
    
    try:
        file_data = await file.read()
        
        service = DocumentService()
        
        filename = file.filename if file.filename else "unknown_file"
        content_type = file.content_type if file.content_type else "application/octet-stream"
        
        result = service.create_document(
            db=db,
            file_data=file_data,
            filename=filename,
            content_type=content_type
        )
        
        return result

    except Exception as e:
        raise HTTPException(  
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки файла: {str(e)}"
        )