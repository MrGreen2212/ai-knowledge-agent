import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_conversation_service, get_rag_service
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationResponse,
)
from app.services.conversation_service import ConversationService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Задать вопрос в диалоге",
    response_description="Ответ ассистента с conversation_id",
    responses={
        404: {"description": "Диалог не найден"},
        422: {"description": "Невалидный запрос (пустой вопрос или неверные параметры)"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Создает новый диалог или продолжает существующий.

    Если conversation_id не указан, создается новый диалог.
    Если conversation_id указан, используется существующий диалог.

    Args:
        request: Запрос с вопросом и параметрами
        db: SQLAlchemy сессия
        conversation_service: Сервис для работы с диалогами
        rag_service: Сервис для генерации ответов

    Returns:
        ChatResponse с conversation_id и ответом

    Raises:
        HTTPException 404: Если указанный диалог не найден
        HTTPException 422: Если вопрос пустой
        HTTPException 500: При других ошибках
    """
    try:
        logger.info(f"Chat request: conversation_id={request.conversation_id}")

        result = conversation_service.chat(
            db=db,
            rag_service=rag_service,
            question=request.question,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            max_tokens=request.max_tokens,
        )

        return ChatResponse(**result)

    except ValueError as e:
        logger.error(f"Conversation not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )


@router.get(
    "",
    response_model=List[ConversationListResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить список диалогов",
    response_description="Список диалогов без сообщений",
    responses={
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
def list_conversations(
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Получает список всех диалогов.

    Диалоги отсортированы по updated_at (новые первыми).

    Args:
        limit: Максимальное количество записей (default: 100)
        offset: Смещение для пагинации (default: 0)
        db: SQLAlchemy сессия
        conversation_service: Сервис для работы с диалогами

    Returns:
        Список диалогов без сообщений
    """
    try:
        conversations = conversation_service.list_conversations(
            db=db,
            limit=limit,
            offset=offset,
        )

        return [ConversationListResponse.from_orm(conv) for conv in conversations]

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations",
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить диалог с сообщениями",
    response_description="Полная информация о диалоге",
    responses={
        404: {"description": "Диалог не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Получает информацию о диалоге с сообщениями.

    Сообщения отсортированы по created_at (старые первыми).

    Args:
        conversation_id: UUID диалога
        db: SQLAlchemy сессия
        conversation_service: Сервис для работы с диалогами

    Returns:
        Полная информация о диалоге с сообщениями

    Raises:
        HTTPException 404: Если диалог не найден
    """
    try:
        conversation = conversation_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with id {conversation_id} not found",
            )

        # Получить сообщения
        messages = conversation_service.get_messages(
            db=db,
            conversation_id=conversation_id,
        )

        # Создать response с сообщениями
        # Используем model_validate для корректной конвертации ORM -> Pydantic
        return ConversationResponse.model_validate(
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "messages": messages,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation",
        )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить диалог",
    responses={
        404: {"description": "Диалог не найден"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Удаляет диалог и все его сообщения.

    Благодаря CASCADE в ForeignKey, все сообщения удаляются автоматически.

    Args:
        conversation_id: UUID диалога
        db: SQLAlchemy сессия
        conversation_service: Сервис для работы с диалогами

    Raises:
        HTTPException 404: Если диалог не найден
    """
    try:
        deleted = conversation_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with id {conversation_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )
