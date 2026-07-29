from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    """Репозиторий для работы с документами в PostgreSQL."""

    def create(
        self,
        db: Session,
        filename: str,
        object_name: str,
        content_type: str,
        size: int,
    ) -> Document:
        """Создает запись о документе в базе данных."""
        document = Document(
            filename=filename,
            object_name=object_name,
            content_type=content_type,
            size=size,
            status="uploaded",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document
