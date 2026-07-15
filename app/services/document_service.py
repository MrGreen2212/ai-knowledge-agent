from typing import Any, Dict

from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.storage import StorageService


class DocumentService:
    def __init__(self):
        self.repository = DocumentRepository()
        self.storage = StorageService()

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