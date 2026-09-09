from sqlalchemy import (
    ARRAY,  # Добавлено для массива эмбеддинга
    BigInteger,
    Column,
    DateTime,
    String,
    Text,  # Добавлено для хранения текста документа
)

# Импортируем специфичные типы именно из диалекта postgresql
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID
from sqlalchemy.sql import func  # <--- ДОБАВИЛИ ЭТОТ ИМПОРТ

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",  # Используем строковое выражение
    )

    filename = Column(String(255), nullable=False)
    object_name = Column(String(500), nullable=False)
    content_type = Column(String(100))
    size = Column(BigInteger)
    status = Column(String(50), nullable=False, default="uploaded")

    # Для времени лучше использовать эту функцию, она учитывает часовой пояс
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Содержание документа (для RAG-системы)
    text = Column(Text)  # Полный текст файла или чанка текста

    # Векторные данные
    embedding = Column(  # type: ignore
        ARRAY(DOUBLE_PRECISION(precision=53)), index=False, nullable=True  # type: ignore
    )
