from typing import List
from uuid import UUID
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

    def list(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """
        Получает список документов с пагинацией.

        Args:
            db: SQLAlchemy сессия
            limit: Максимальное количество документов
            offset: Смещение

        Returns:
            Список документов
        """
        return (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_id(
        self,
        db: Session,
        document_id: UUID,
    ) -> Document | None:
        """
        Получает документ по ID.

        Args:
            db: SQLAlchemy сессия
            document_id: ID документа

        Returns:
            Документ или None, если документ не найден
        """
        return (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def delete(
        self,
        db: Session,
        document_id: UUID,
    ) -> bool:
        """Удаляет документ из базы данных."""
        document = self.get_by_id(db=db, document_id=document_id)

        if document is None:
            return False

        db.delete(document)
        db.commit()

        return True
