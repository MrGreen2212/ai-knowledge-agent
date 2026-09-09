from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Запрос на создание или продолжение диалога."""

    question: str = Field(..., min_length=1, max_length=5000, description="Вопрос пользователя")
    conversation_id: Optional[UUID] = Field(
        None, description="UUID существующего диалога (опционально)"
    )
    top_k: int = Field(3, ge=1, le=10, description="Количество релевантных документов")
    max_tokens: int = Field(
        512, ge=1, le=2048, description="Максимальное количество токенов для ответа"
    )

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        """Удаляет пробелы в начале и конце вопроса."""
        return v.strip()


class ChatResponse(BaseModel):
    """Ответ на вопрос пользователя."""

    conversation_id: UUID
    answer: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Сообщение в диалоге."""

    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Краткая информация о диалоге для списка."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Полная информация о диалоге с сообщениями."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True
