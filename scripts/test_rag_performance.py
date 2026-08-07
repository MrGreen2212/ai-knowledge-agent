"""
Скрипт для тестирования производительности RAG с подробным логированием.

Использование:
    python scripts/test_rag_performance.py
"""
import logging
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.dependencies import get_rag_service

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rag_performance_test.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def test_rag_answer():
    """Тестирует генерацию ответа с подробным логированием."""
    
    logger.info("=" * 100)
    logger.info("STARTING RAG PERFORMANCE TEST")
    logger.info("=" * 100)
    
    # Получаем сервис
    logger.info("Initializing RAG service...")
    rag = get_rag_service()
    
    # Тестовый вопрос
    question = "Что такое UML?"
    
    logger.info(f"\nTest question: {question}")
    logger.info(f"Question length: {len(question)} chars\n")
    
    try:
        # Выполняем запрос
        logger.info("Calling rag.answer()...")
        answer = rag.answer(question, top_k=3, max_tokens=512)
        
        logger.info("\n" + "=" * 100)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 100)
        logger.info(f"\nFinal answer:\n{answer}\n")
        logger.info("=" * 100)
        
        return answer
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    test_rag_answer()
