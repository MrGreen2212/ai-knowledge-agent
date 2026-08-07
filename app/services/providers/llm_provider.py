"""
Абстрактный интерфейс для LLM провайдеров.

Определяет контракт для всех реализаций LLM (Ollama, OpenAI, Anthropic и т.д.).
Следует принципу Dependency Inversion Principle (DIP) из SOLID.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Абстрактный базовый класс для LLM провайдеров.
    
    Определяет минимальный контракт для генерации текста с помощью языковых моделей.
    Любая реализация (Ollama, OpenAI, Anthropic, etc.) должна реализовать этот интерфейс.
    
    Принципы:
    - Interface Segregation Principle: минимальный необходимый интерфейс
    - Dependency Inversion Principle: зависимость от абстракции, а не от конкретной реализации
    - Open/Closed Principle: открыт для расширения (новые провайдеры), закрыт для модификации
    """
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Генерирует текст на основе промпта.
        
        Args:
            prompt: Текст запроса для генерации ответа
            max_tokens: Максимальное количество токенов для генерации
            
        Returns:
            Сгенерированный текст ответа от модели
            
        Raises:
            ConnectionError: Если не удалось подключиться к LLM сервису
            LLMProviderError: Если произошла ошибка при генерации
        """
        pass
