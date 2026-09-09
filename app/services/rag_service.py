import logging
import time
from typing import List, Optional
from uuid import UUID

from app.exceptions.providers import LLMProviderError

from .providers import EmbeddingProvider, LLMProvider, StorageProvider, VectorStoreProvider
from .text_extraction_service import TextExtractionService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Полный RAG pipeline для индексации и поиска документов.

    Следует принципам Clean Architecture и Dependency Inversion Principle:
    - Зависит от абстракций (LLMProvider, EmbeddingProvider, VectorStoreProvider, StorageProvider)
    - Не знает о конкретных технологиях (Ollama, FastEmbed, Chroma, MinIO)
    - Легко заменить провайдеров без изменения бизнес-логики
    """

    CHUNK_SIZE = 500
    MAX_CONTEXT_LENGTH = 6000  # Максимальный размер контекста в символах

    # Веса Hybrid Search ranking.
    # Semantic search (dense embeddings) обычно точнее улавливает смысл запроса,
    # поэтому ему отдан больший вес (0.6). Lexical search (точные/префиксные
    # совпадения токенов) хорошо дополняет его для редких терминов, аббревиатур
    # и точных фраз, которые embedding модель может "размыть" — вес 0.4.
    # Сумма весов равна 1.0, поэтому итоговый hybrid_score остаётся в диапазоне 0..1,
    # если обе relevance-компоненты лежат в 0..1.
    SEMANTIC_WEIGHT = 0.6
    LEXICAL_WEIGHT = 0.4

    # Во сколько раз расширяем кандидатов semantic/lexical поиска относительно
    # финального limit, чтобы после слияния и ranking было из чего выбирать топ.
    CANDIDATE_POOL_MULTIPLIER = 3

    def __init__(
        self,
        storage: StorageProvider,
        extractor: TextExtractionService,
        embedding: EmbeddingProvider,
        vector_store: VectorStoreProvider,
        llm: Optional[LLMProvider] = None,
    ):
        """
        Инициализирует RAG сервис.

        Args:
            storage: Storage провайдер для работы с хранилищем файлов
            extractor: Сервис для извлечения текста из документов
            embedding: Embedding провайдер для создания эмбеддингов
            vector_store: Vector Store провайдер для работы с векторной БД
            llm: LLM провайдер для генерации ответов (опционально)
        """
        self.storage = storage
        self.extractor = extractor
        self.embedding = embedding
        self.vector_store = vector_store
        self.llm = llm

    def process_document(self, object_name: str, document_id: UUID | str) -> None:
        """Индексирует документ в векторную базу данных."""
        logger.info(f"Processing document: {object_name}")

        file_data = self.storage.get_file(object_name)
        logger.debug(f"File retrieved from storage: {len(file_data)} bytes")

        text = self.extractor.extract(file_data=file_data, filename=object_name)

        if not text.strip():
            raise ValueError("Не удалось извлечь текст из документа.")

        chunks = self._split_text(text)
        logger.info(f"Document split into {len(chunks)} chunks")

        embeddings = self.embedding.embed_documents(chunks)
        logger.debug(f"Generated {len(embeddings)} embeddings")

        document_id = str(document_id)
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "object_name": object_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        self.vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        logger.info(f"Document indexed successfully: {object_name}")

    def search(self, query: str, limit: int = 3):
        """
        Выполняет Hybrid Search: объединяет semantic (векторный) и lexical
        (полнотекстовый) поиск в единый ранжированный список результатов.

        Алгоритм:
        1. Получаем расширенные пулы кандидатов (limit * CANDIDATE_POOL_MULTIPLIER)
           отдельно от semantic (`vector_store.query`) и lexical
           (`vector_store.lexical_search`) поиска.
        2. Объединяем кандидатов, дедуплицируя строго по chunk `id`
           (а не по тексту/document_id/chunk_index — один и тот же chunk может
           быть найден обоими поисками и должен учитываться один раз).
        3. Semantic search в Chroma возвращает cosine distance (0 = идентично,
           больше = хуже), а нам нужна relevance, где больше = лучше.
           Используется point-wise преобразование semantic_relevance = 1 / (1 + distance):
           оно не зависит от размера candidate pool и от того, какие ещё
           кандидаты попали в выборку (в отличие от rank-based нормализации,
           где relevance одного и того же chunk менялась в зависимости от
           количества и состава кандидатов). distance=0 даёт relevance=1.0
           (лучший случай), с ростом distance relevance монотонно убывает,
           оставаясь в диапазоне (0, 1].
        4. Lexical score уже находится в диапазоне 0..1 (доля совпавших
           токенов запроса), поэтому используется напрямую как lexical relevance.
        5. Для каждого уникального chunk считается:
               hybrid_score = SEMANTIC_WEIGHT * semantic_relevance
                            + LEXICAL_WEIGHT * lexical_relevance
           Если chunk найден только одним из поисков, недостающая
           relevance-компонента считается равной 0.
        6. Результаты сортируются по hybrid_score по убыванию, возвращается top `limit`.

        Важно: результирующий "score" — это hybrid_score (относительная
        релевантность в рамках текущего запроса), а НЕ исходный Chroma
        cosine distance и не сырой lexical score.
        """
        logger.info(f"Searching for: {query}")

        candidate_limit = limit * self.CANDIDATE_POOL_MULTIPLIER

        vector = self.embedding.embed_query(query)
        semantic_results = self.vector_store.query(embedding=vector, limit=candidate_limit)
        lexical_results = self.vector_store.lexical_search(query=query, limit=candidate_limit)

        semantic_relevance_by_id = {
            result["id"]: self._distance_to_semantic_relevance(result["score"])
            for result in semantic_results
        }
        lexical_relevance_by_id = {
            result["id"]: float(result["score"]) for result in lexical_results
        }

        # Объединяем кандидатов, строго дедуплицируя по id chunk'а.
        chunks_by_id = {}
        for result in (*semantic_results, *lexical_results):
            chunks_by_id.setdefault(result["id"], result)

        hybrid_results = []
        for chunk_id, chunk in chunks_by_id.items():
            semantic_relevance = semantic_relevance_by_id.get(chunk_id, 0.0)
            lexical_relevance = lexical_relevance_by_id.get(chunk_id, 0.0)
            hybrid_score = (
                self.SEMANTIC_WEIGHT * semantic_relevance
                + self.LEXICAL_WEIGHT * lexical_relevance
            )

            hybrid_results.append(
                {
                    "id": chunk_id,
                    "score": hybrid_score,
                    "text": chunk["text"],
                    "metadata": {
                        **(chunk.get("metadata") or {}),
                        "semantic_relevance": semantic_relevance,
                        "lexical_relevance": lexical_relevance,
                        "hybrid_score": hybrid_score,
                    },
                }
            )

        hybrid_results.sort(key=lambda result: result["score"], reverse=True)
        results = hybrid_results[:limit]

        logger.info(f"Found {len(results)} results")

        return results

    @staticmethod
    def _rank_based_semantic_relevance(semantic_results: List[dict]) -> dict:
        """
        Преобразует semantic search результаты (Chroma cosine distance,
        меньше = лучше) в relevance (больше = лучше) через rank-based
        нормализацию: лучший по расстоянию кандидат получает 1.0, худший — 0.0,
        промежуточные — линейно по позиции в отсортированном по distance списке.

        Rank-based подход используется вместо прямой инверсии (1 - distance),
        так как абсолютный диапазон cosine distance зависит от embedding модели
        и не гарантированно лежит в [0, 1], что сделало бы score несравнимым
        с lexical relevance.
        """
        if not semantic_results:
            return {}

        ordered = sorted(semantic_results, key=lambda result: result["score"])
        count = len(ordered)

        if count == 1:
            return {ordered[0]["id"]: 1.0}

        relevance_by_id = {}
        for rank, result in enumerate(ordered):
            relevance_by_id[result["id"]] = 1.0 - (rank / (count - 1))

        return relevance_by_id

    def answer(
        self,
        question: str,
        top_k: int = 3,
        max_tokens: int = 512,
        history: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
        history_message_count: int = 0,
    ) -> str:
        """
        Генерирует ответ на вопрос используя RAG + LLM.

        Процесс:
        1. Выполняет семантический поиск по векторной базе
        2. Получает top-k релевантных фрагментов документов
        3. Формирует контекст из найденных фрагментов
        4. Создает промпт для LLM с контекстом, историей и вопросом
        5. Отправляет промпт в Ollama для генерации ответа

        Args:
            question: Вопрос пользователя
            top_k: Количество релевантных фрагментов для контекста
            max_tokens: Максимальное количество токенов для генерации ответа (default: 512)
            history: Отформатированная история диалога (опционально)

        Returns:
            Сгенерированный ответ от LLM на основе найденных документов

        Raises:
            LLMProviderError: Если LLM провайдер не инициализирован
            ValueError: Если не найдено релевантных документов
        """
        start_time = time.time()

        if not self.llm:
            logger.error("LLM provider not initialized")
            raise LLMProviderError(
                "LLM провайдер не инициализирован. "
                "Убедитесь, что провайдер передан в конструктор RAGService."
            )

        logger.info("=" * 80)
        logger.info("STARTING RAG ANSWER GENERATION")
        logger.info(f"Question: {question}")
        logger.info(f"Parameters: top_k={top_k}, max_tokens={max_tokens}")
        logger.info(
            "RAG DIAGNOSTIC request: conversation_id=%s, history_messages=%d",
            conversation_id,
            history_message_count,
        )
        logger.info("=" * 80)

        # Шаг 1: Поиск релевантных документов
        search_start = time.time()
        search_results = self.search(query=question, limit=top_k)
        search_time = time.time() - search_start

        collection_count = getattr(self.vector_store, "count", None)
        if callable(collection_count):
            try:
                logger.info("RAG DIAGNOSTIC Chroma collection_count=%s", collection_count())
            except Exception as exc:
                logger.warning("RAG DIAGNOSTIC Chroma collection_count=unavailable: %s", exc)
        else:
            logger.info("RAG DIAGNOSTIC Chroma collection_count=unavailable")

        for result_index, result in enumerate(search_results, 1):
            metadata = result.get("metadata", {}) or {}
            preview = str(result.get("text", ""))[:300].replace("\n", " ")
            logger.info(
                "RAG DIAGNOSTIC result[%d]: document_id=%s, object_name=%s, "
                "chunk_index=%s, distance=%s, text_preview=%r",
                result_index,
                metadata.get("document_id"),
                metadata.get("object_name"),
                metadata.get("chunk_index"),
                result.get("score"),
                preview,
            )

        logger.info("RAG DIAGNOSTIC found_chunks=%d", len(search_results))

        logger.debug(f"⏱️  SEARCH TIME: {search_time:.3f} seconds")

        if not search_results:
            logger.warning("No relevant documents found")
            raise ValueError("Не найдено релевантных документов для ответа на вопрос.")

        # Шаг 2: Формирование контекста из найденных фрагментов с ограничением размера
        context_start = time.time()
        context_parts = []
        current_length = 0
        chunks_used = 0

        logger.debug("\n📊 CHUNK ANALYSIS:")
        for idx, result in enumerate(search_results, 1):
            text = result.get("text", "")
            score = result.get("score", 0)
            metadata = result.get("metadata", {})
            doc_id = metadata.get("document_id", "unknown")

            # Анализ размера чанка
            chunk_chars = len(text)
            chunk_tokens_approx = chunk_chars // 4  # Примерно 1 токен = 4 символа

            logger.debug(
                f"  Chunk {idx}: {chunk_chars} chars, ~{chunk_tokens_approx} tokens, "
                f"score={score:.3f}, doc_id={doc_id}"
            )

            # Формируем фрагмент с метаданными
            chunk_text = f"[Документ {idx}, ID: {doc_id}, релевантность: {score:.3f}]\n{text}"
            chunk_length = len(chunk_text)

            # Проверяем, не превысим ли лимит
            if current_length + chunk_length + 2 > self.MAX_CONTEXT_LENGTH:  # +2 для "\n\n"
                logger.debug(
                    f"⚠️  Context limit reached: {current_length} chars. "
                    f"Skipping remaining {len(search_results) - chunks_used} chunks."
                )
                break

            context_parts.append(chunk_text)
            current_length += chunk_length + 2  # +2 для разделителя "\n\n"
            chunks_used += 1

        context = "\n\n".join(context_parts)
        context_time = time.time() - context_start
        context_tokens_approx = len(context) // 4
        context_document_ids = [
            (result.get("metadata", {}) or {}).get("document_id")
            for result in search_results[:chunks_used]
        ]

        logger.info(
            "RAG DIAGNOSTIC context_document_ids=%s, context_length=%d",
            context_document_ids,
            len(context),
        )

        logger.debug(f"\n⏱️  CONTEXT BUILD TIME: {context_time:.3f} seconds")
        logger.debug(
            f"📝 CONTEXT STATS: {chunks_used}/{len(search_results)} chunks used, "
            f"{len(context)} chars, ~{context_tokens_approx} tokens"
        )

        # Шаг 3: Формирование промпта для LLM
        prompt_start = time.time()
        prompt = self._build_prompt(question=question, context=context, history=history)
        prompt_time = time.time() - prompt_start
        prompt_tokens_approx = len(prompt) // 4

        logger.info("RAG DIAGNOSTIC prompt_length=%d", len(prompt))

        logger.debug(f"\n⏱️  PROMPT BUILD TIME: {prompt_time:.3f} seconds")
        logger.debug(f"📄 PROMPT STATS: {len(prompt)} chars, ~{prompt_tokens_approx} tokens")
        logger.debug(f"   Question: {len(question)} chars")
        logger.debug(f"   Context: {len(context)} chars")
        logger.debug(f"   Template overhead: {len(prompt) - len(context) - len(question)} chars")

        # Шаг 4: Генерация ответа через LLM
        logger.debug("\n🚀 SENDING TO LLM...")
        llm_start = time.time()

        try:
            answer = self.llm.generate(prompt, max_tokens=max_tokens)
            llm_time = time.time() - llm_start

            logger.debug(f"⏱️  LLM GENERATION TIME: {llm_time:.3f} seconds")
            logger.debug(f"✅ Answer: {len(answer)} chars")

            total_time = time.time() - start_time
            logger.info("\n" + "=" * 80)
            logger.info("⏱️  TOTAL TIME BREAKDOWN:")
            logger.info(f"   Search:     {search_time:7.3f}s ({search_time/total_time*100:5.1f}%)")
            logger.info(
                f"   Context:    {context_time:7.3f}s ({context_time/total_time*100:5.1f}%)"
            )
            logger.info(f"   Prompt:     {prompt_time:7.3f}s ({prompt_time/total_time*100:5.1f}%)")
            logger.info(f"   LLM:        {llm_time:7.3f}s ({llm_time/total_time*100:5.1f}%)")
            logger.info("   ─────────────────────────────")
            logger.info(f"   TOTAL:      {total_time:7.3f}s")
            logger.info("=" * 80)

            return answer
        except Exception as e:
            logger.error(f"❌ Failed to generate answer: {e}")
            raise

    def _build_prompt(
        self,
        question: str,
        context: str,
        history: Optional[str] = None,
    ) -> str:
        """
        Формирует промпт для LLM с контекстом, историей и вопросом.

        Args:
            question: Вопрос пользователя
            context: Контекст из найденных документов
            history: Отформатированная история диалога (опционально)

        Returns:
            Сформированный промпт для LLM
        """
        prompt_parts = [
            "Ты - AI ассистент, который отвечает на вопросы на основе предоставленных документов."
        ]

        # Добавить историю если есть
        if history:
            prompt_parts.append(f"\nИстория диалога:\n{history}")

        # Добавить контекст документов
        prompt_parts.append(f"\nКонтекст из документов:\n{context}")

        # Добавить текущий вопрос
        prompt_parts.append(f"\nВопрос пользователя: {question}")

        # Инструкции
        instructions = """
Инструкции:
- Отвечай только на основе предоставленного контекста
- Учитывай историю диалога для понимания контекста вопроса
- Если в контексте нет информации для ответа, честно скажи об этом
- Будь точным и конкретным
- Используй информацию из всех релевантных документов
- Отвечай на русском языке

Ответ:"""
        prompt_parts.append(instructions)

        return "\n".join(prompt_parts)

    def _split_text(self, text: str) -> List[str]:
        """Разбивает текст на фрагменты фиксированного размера."""
        chunks = []
        current_chunk = ""

        for sentence in text.split("\n"):
            words_in_current = len(current_chunk.split())

            if words_in_current < self.CHUNK_SIZE or current_chunk == "":
                current_chunk += "\n" + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
