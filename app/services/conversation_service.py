import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Сервис для управления диалогами и сообщениями.

    Ответственность:
    - Управление жизненным циклом диалогов (создание, получение, удаление)
    - Управление сообщениями в диалогах
    - Обновление метаданных диалогов
    - Оркестрация RAG с историей диалогов

    НЕ отвечает за:
    - Генерацию ответов (это RAGService)
    - Работу с LLM (это LLMProvider)
    - RAG-поиск (это RAGService)
    """

    MAX_HISTORY_MESSAGES = 10

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    def create_conversation(
        self,
        db: Session,
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Создает новый диалог.

        Args:
            db: SQLAlchemy сессия
            title: Название диалога (опционально)

        Returns:
            Созданный объект Conversation
        """
        logger.info(f"Creating new conversation with title: {title}")

        conversation = self.conversation_repository.create(
            db=db,
            title=title,
        )

        logger.info(f"Conversation created: {conversation.id}")
        return conversation

    def get_conversation(
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
        conversation = self.conversation_repository.get_by_id(
            db=db,
            conversation_id=conversation_id,
        )

        if conversation is None:
            logger.warning(f"Conversation not found: {conversation_id}")

        return conversation

    def list_conversations(
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
        conversations = self.conversation_repository.list(
            db=db,
            limit=limit,
            offset=offset,
        )

        return conversations

    def delete_conversation(
        self,
        db: Session,
        conversation_id: UUID,
    ) -> bool:
        """
        Удаляет диалог и все его сообщения.

        Благодаря CASCADE в ForeignKey, все сообщения будут удалены автоматически.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога

        Returns:
            True если диалог был удален, False если не найден
        """
        logger.info(f"Deleting conversation: {conversation_id}")

        deleted = self.conversation_repository.delete(
            db=db,
            conversation_id=conversation_id,
        )

        if deleted:
            logger.info(f"Conversation deleted: {conversation_id}")
        else:
            logger.warning(f"Conversation not found for deletion: {conversation_id}")

        return deleted

    def add_message(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:
        """
        Добавляет сообщение в диалог и обновляет updated_at диалога.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            role: Роль отправителя ('user' или 'assistant')
            content: Содержимое сообщения

        Returns:
            Созданный объект Message
        """
        logger.info(f"Adding message to conversation {conversation_id}: role={role}")

        try:
            # Добавляем сообщение (БЕЗ commit)
            message = self.message_repository.create_without_commit(
                db=db,
                conversation_id=conversation_id,
                role=role,
                content=content,
            )

            # Обновляем updated_at диалога (БЕЗ commit)
            updated = self.conversation_repository.touch_without_commit(
                db=db,
                conversation_id=conversation_id,
            )

            if not updated:
                # Диалог не найден - откатываем транзакцию
                db.rollback()
                logger.error(f"Conversation not found: {conversation_id}")
                raise ValueError(f"Conversation with id {conversation_id} not found")

            # Один commit для обеих операций
            db.commit()
            db.refresh(message)

            logger.info(f"Message added: {message.id}")
            return message

        except Exception as e:
            # Откатываем транзакцию при любой ошибке
            db.rollback()
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            raise

    def get_messages(
        self,
        db: Session,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        """
        Получает историю сообщений диалога.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            limit: Максимальное количество записей (default: 100)
            offset: Смещение для пагинации (default: 0)

        Returns:
            Список объектов Message, отсортированных по created_at (старые первыми)
        """
        messages = self.message_repository.list_by_conversation(
            db=db,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )

        return messages

    def rename_conversation(
        self,
        db: Session,
        conversation_id: UUID,
        title: str,
    ) -> Optional[Conversation]:
        """
        Переименовывает диалог.

        Args:
            db: SQLAlchemy сессия
            conversation_id: UUID диалога
            title: Новое название диалога

        Returns:
            Обновленный объект Conversation или None, если не найден
        """
        logger.info(f"Renaming conversation {conversation_id} to: {title}")

        conversation = self.conversation_repository.update(
            db=db,
            conversation_id=conversation_id,
            title=title,
        )

        if conversation is None:
            logger.warning(f"Conversation not found for rename: {conversation_id}")
        else:
            logger.info(f"Conversation renamed: {conversation_id}")

        return conversation

    def chat(
        self,
        db: Session,
        rag_service,
        question: str,
        conversation_id: Optional[UUID] = None,
        top_k: int = 3,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        """
        Обрабатывает вопрос пользователя с использованием RAG и истории диалога.

        Процесс:
        1. Создает новый диалог или использует существующий
        2. Получает историю последних N сообщений
        3. Форматирует историю для LLM
        4. Вызывает RAGService для генерации ответа (БЕЗ открытой транзакции)
        5. Сохраняет вопрос и ответ в одной транзакции

        Args:
            db: SQLAlchemy сессия
            rag_service: Экземпляр RAGService для генерации ответов
            question: Вопрос пользователя
            conversation_id: UUID существующего диалога (опционально)
            top_k: Количество релевантных документов для контекста
            max_tokens: Максимальное количество токенов для ответа

        Returns:
            Dict с полями:
                - conversation_id: UUID диалога
                - answer: Ответ ассистента

        Raises:
            ValueError: Если диалог не найден
        """
        logger.info("Processing chat question")

        # Шаг 1: Создать или получить диалог
        if conversation_id is None:
            conversation = self.create_conversation(db=db)
            conversation_id = conversation.id  # type: ignore[assignment]
            logger.info(f"Created new conversation: {conversation_id}")
        else:
            conversation_or_none = self.get_conversation(db=db, conversation_id=conversation_id)
            if conversation_or_none is None:
                logger.error(f"Conversation not found: {conversation_id}")
                raise ValueError(f"Conversation with id {conversation_id} not found")
            # После проверки conversation точно не None
            conversation = conversation_or_none
            logger.info(f"Using existing conversation: {conversation_id}")

        # Шаг 2: Получить историю
        # conversation_id здесь гарантированно UUID (не None)
        assert conversation_id is not None
        messages = self.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=self.MAX_HISTORY_MESSAGES,
        )
        logger.info(f"Retrieved {len(messages)} messages from history")

        # Шаг 3: Форматировать историю
        history = self._format_history(messages) if messages else None

        # Шаг 4: Генерация ответа через RAG
        # ВАЖНО: Здесь НЕТ открытой транзакции
        # LLM может работать 5-30 секунд, нельзя держать транзакцию открытой
        logger.info(f"Calling RAGService with top_k={top_k}, max_tokens={max_tokens}")
        answer = rag_service.answer(
            question=question,
            top_k=top_k,
            max_tokens=max_tokens,
            history=history,
            conversation_id=conversation_id,
            history_message_count=len(messages),
        )
        logger.info(f"Generated answer: {len(answer)} characters")

        # Шаг 5: Сохранить оба сообщения в ОДНОЙ транзакции
        try:
            # Создать сообщение пользователя БЕЗ commit
            self.message_repository.create_without_commit(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=question,
            )

            # Создать сообщение ассистента БЕЗ commit
            self.message_repository.create_without_commit(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
            )

            # Обновить updated_at диалога БЕЗ commit (один раз)
            updated = self.conversation_repository.touch_without_commit(
                db=db,
                conversation_id=conversation_id,
            )

            if not updated:
                db.rollback()
                logger.error(f"Conversation not found during save: {conversation_id}")
                raise ValueError(f"Conversation with id {conversation_id} not found")

            # ОДИН commit для всех операций
            db.commit()

            logger.info("User and assistant messages saved successfully")

            return {
                "conversation_id": conversation_id,
                "answer": answer,
            }

        except Exception as e:
            # Откатываем транзакцию при ошибке сохранения
            db.rollback()
            logger.error(f"Failed to save messages: {e}")
            raise

    def _format_history(self, messages: List[Message]) -> str:
        """
        Форматирует историю сообщений для передачи в LLM.

        Args:
            messages: Список сообщений (отсортированы по created_at)

        Returns:
            Отформатированная история в виде строки
        """
        if not messages:
            return ""

        history_parts = []
        for msg in messages:
            # Пропускаем пустые сообщения
            content = msg.content.strip() if msg.content else ""
            if not content:
                continue

            role_label = "User" if msg.role == "user" else "Assistant"
            history_parts.append(f"{role_label}: {content}")

        return "\n\n".join(history_parts)
