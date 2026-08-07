from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    """Репозиторий для работы с сообщениями в PostgreSQL."""

    def create(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """
        Создает новое сообщение в базе данных с автоматическим commit.
        
        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога, к которому относится сообщение
            role: Роль отправителя ('user' или 'assistant')
            content: Содержимое сообщения
            
        Returns:
            Созданный объект Message
        """
        message = self.create_without_commit(
            db=db,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        
        db.commit()
        db.refresh(message)
        
        return message

    def create_without_commit(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """
        Создает сообщение БЕЗ commit.
        
        ВАЖНО: НЕ выполняет commit - вызывающий код должен сделать commit самостоятельно.
        Используется для выполнения нескольких операций в одной транзакции.
        
        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога, к которому относится сообщение
            role: Роль отправителя ('user' или 'assistant')
            content: Содержимое сообщения
            
        Returns:
            Созданный объект Message (БЕЗ commit, БЕЗ flush)
            
        Note:
            Метод НЕ вызывает flush(), так как:
            - flush() будет выполнен автоматически перед commit()
            - Преждевременный flush() может вызвать IntegrityError до завершения транзакции
            - Позволяет вызывающему коду контролировать момент отправки в БД
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        
        db.add(message)
        
        return message

    def list_by_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        """
        Получает последние N сообщений для конкретного диалога.
        
        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            limit: Максимальное количество записей (default: 100)
            offset: Смещение для пагинации (default: 0)
            
        Returns:
            Список последних N объектов Message, отсортированных по created_at (старые первыми)
            
        Note:
            Сначала выбираются последние N сообщений (ORDER BY DESC + LIMIT),
            затем результат разворачивается для хронологического порядка в промпте.
            Это гарантирует, что в контекст LLM попадают самые свежие сообщения.
        """
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()  # Новые первыми для LIMIT
        ).limit(limit).offset(offset).all()
        
        # Развернуть для хронологического порядка (старые → новые)
        return list(reversed(messages))

    def delete_by_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> int:
        """
        Удаляет все сообщения конкретного диалога.
        
        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            
        Returns:
            Количество удаленных сообщений
            
        Note:
            Этот метод обычно не нужен, так как CASCADE в ForeignKey автоматически
            удаляет сообщения при удалении диалога. Однако может быть полезен
            для очистки истории диалога без удаления самого диалога.
        """
        deleted_count = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()

        db.commit()

        return deleted_count
