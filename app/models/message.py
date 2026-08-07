from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Message(Base):
    """
    Модель сообщения в диалоге.
    
    Хранит отдельное сообщение в рамках диалога.
    Может быть сообщением пользователя (role='user') или ассистента (role='assistant').
    """
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID диалога, к которому относится сообщение"
    )

    role = Column(
        String(20),
        nullable=False,
        comment="Роль отправителя: 'user' (пользователь) или 'assistant' (AI ассистент)"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Содержимое сообщения"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания сообщения"
    )

    # Relationship: сообщение принадлежит одному диалогу
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )

    # Индексы и ограничения для оптимизации запросов и валидации данных
    __table_args__ = (
        # Индекс для быстрого поиска сообщений по диалогу
        Index("idx_messages_conversation", "conversation_id"),
        # Композитный индекс для запросов "все сообщения диалога, отсортированные по времени"
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        # Ограничение на допустимые значения role
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_message_role"
        ),
    )

    def __repr__(self):
        preview = (self.content or "")[:50]
        content_preview = preview + "..." if len(self.content or "") > 50 else preview
        return f"<Message(id={self.id}, role={self.role}, content='{content_preview}')>"
