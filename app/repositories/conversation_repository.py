from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    """Репозиторий для работы с диалогами в PostgreSQL."""

    def create(
        self,
        db: Session,
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Создает новый диалог в базе данных.

        Args:
            db: SQLAlchemy сессия
            title: Название диалога (опционально)

        Returns:
            Созданный объект Conversation
        """
        conversation = Conversation(title=title)

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    def get_by_id(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """
        Получает диалог по ID.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога

        Returns:
            Объект Conversation или None, если не найден
        """
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def list(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        Получает список всех диалогов с пагинацией.

        Args:
            db: SQLAlchemy сессия
            limit: Максимальное количество записей (default: 100)
            offset: Смещение для пагинации (default: 0)

        Returns:
            Список объектов Conversation, отсортированных по updated_at (новые первыми)
        """
        return (
            db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update(
        self,
        db: Session,
        conversation_id: UUID,
        title: Optional[str] = None,
    ) -> Optional[Conversation]:
        """
        Обновляет диалог.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            title: Новое название диалога (опционально)

        Returns:
            Обновленный объект Conversation или None, если не найден
        """
        conversation = self.get_by_id(db, conversation_id)

        if conversation is None:
            return None

        if title is not None:
            conversation.title = title  # type: ignore[assignment]

        db.commit()
        db.refresh(conversation)

        return conversation

    def delete(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> bool:
        """
        Удаляет диалог из базы данных.

        Благодаря CASCADE в ForeignKey, все связанные сообщения будут удалены автоматически.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога

        Returns:
            True если диалог был удален, False если не найден
        """
        conversation = self.get_by_id(db, conversation_id)

        if conversation is None:
            return False

        db.delete(conversation)
        db.commit()

        return True

    def touch_without_commit(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> bool:
        """
        Обновляет updated_at диалога на текущее время БЕЗ commit.

        ВАЖНО: НЕ выполняет commit - вызывающий код должен сделать commit самостоятельно.
        Используется для выполнения нескольких операций в одной транзакции.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога

        Returns:
            True если диалог найден и обновлен, False если не найден

        Note:
            Использует func.now() для генерации времени на стороне БД.
            SQLAlchemy корректно обрабатывает присваивание func.now() через ORM
            и генерирует SQL: UPDATE conversations SET updated_at = NOW() ...
        """
        from sqlalchemy.sql import func

        conversation = self.get_by_id(db, conversation_id)

        if conversation is None:
            return False

        conversation.updated_at = func.now()  # type: ignore[assignment]
        return True
