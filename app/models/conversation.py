from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Conversation(Base):
    """
    Модель диалога (conversation).
    
    Хранит информацию о диалоге пользователя с AI ассистентом.
    Один диалог может содержать множество сообщений (messages).
    """
    __tablename__ = "conversations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    title = Column(
        String(255),
        nullable=True,
        comment="Название диалога (опционально, может генерироваться автоматически)"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания диалога"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Дата и время последнего обновления диалога (обновляется вручную при добавлении сообщений)"
    )

    # Relationship: один диалог содержит множество сообщений
    # cascade="all, delete-orphan" обеспечивает удаление всех сообщений при удалении диалога
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, created_at={self.created_at})>"
