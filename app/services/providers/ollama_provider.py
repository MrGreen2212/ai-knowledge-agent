"""
Ollama реализация LLMProvider.

Конкретная реализация интерфейса LLMProvider для работы с Ollama.
"""

import logging
import time
from typing import Optional

import requests

from app.core.config import settings
from app.exceptions.providers import LLMGenerationError, LLMConnectionError, LLMTimeoutError
from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama реализация LLMProvider.
    
    Взаимодействует с Ollama через HTTP API для генерации текста.
    Реализует интерфейс LLMProvider, следуя принципу Liskov Substitution Principle (LSP).
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Инициализирует Ollama провайдер.
        
        Args:
            base_url: URL Ollama сервиса (по умолчанию из settings)
            model: Название модели (по умолчанию из settings)
        """
        self.base_url = base_url or settings.OLLAMA_URL
        self.model = model or settings.OLLAMA_MODEL
        logger.info(f"OllamaProvider initialized with URL: {self.base_url}, Model: {self.model}")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Генерирует текст используя Ollama.
        
        Args:
            prompt: Текст запроса для генерации ответа
            max_tokens: Максимальное количество токенов для генерации
            
        Returns:
            Сгенерированный текст ответа от модели
            
            Raises:
            LLMConnectionError: Если не удалось подключиться к Ollama
            LLMTimeoutError: Если превышено время ожидания
            LLMGenerationError: Если произошла ошибка при генерации
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": 30,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1,
                "num_ctx": 4096,
                "num_thread": 4
            }
        }

        try:
            request_start = time.time()
            logger.debug(f"📤 Sending request to Ollama: {url}")
            logger.debug(f"   Prompt length: {len(prompt)} chars")
            logger.debug(f"   Max tokens: {max_tokens}")
            logger.debug(f"   Model: {self.model}")
            
            response = requests.post(url, json=payload, timeout=None)
            request_time = time.time() - request_start
            
            logger.debug(f"⏱️  HTTP REQUEST TIME: {request_time:.3f} seconds")
            
            # Проверка HTTP 500 и других ошибок
            if response.status_code == 500:
                error_text = response.text[:500] if response.text else "No response body"
                logger.error(f"Ollama returned HTTP 500. Response: {error_text}")
                raise LLMGenerationError(
                    f"Ollama вернул ошибку сервера (HTTP 500). "
                    f"Возможно, промпт слишком длинный или модель перегружена. "
                    f"Ответ сервера: {error_text}"
                )
            
            response.raise_for_status()

            parse_start = time.time()
            result = response.json()
            parse_time = time.time() - parse_start
            
            generated_text = result.get("response", "")
            
            # Дополнительная статистика из Ollama
            total_duration = result.get("total_duration", 0) / 1e9  # наносекунды в секунды
            load_duration = result.get("load_duration", 0) / 1e9
            prompt_eval_count = result.get("prompt_eval_count", 0)
            prompt_eval_duration = result.get("prompt_eval_duration", 0) / 1e9
            eval_count = result.get("eval_count", 0)
            eval_duration = result.get("eval_duration", 0) / 1e9
            
            logger.debug(f"⏱️  JSON PARSE TIME: {parse_time:.3f} seconds")
            logger.debug(f"\n📊 OLLAMA INTERNAL STATS:")
            logger.debug(f"   Total duration:        {total_duration:.3f}s")
            logger.debug(f"   Model load duration:   {load_duration:.3f}s")
            logger.debug(f"   Prompt eval tokens:    {prompt_eval_count}")
            logger.debug(f"   Prompt eval duration:  {prompt_eval_duration:.3f}s")
            if prompt_eval_count > 0:
                logger.debug(f"   Prompt eval speed:     {prompt_eval_count/prompt_eval_duration:.1f} tokens/s")
            logger.debug(f"   Response tokens:       {eval_count}")
            logger.debug(f"   Response duration:     {eval_duration:.3f}s")
            if eval_count > 0:
                logger.debug(f"   Response speed:        {eval_count/eval_duration:.1f} tokens/s")

            if not generated_text:
                logger.warning("Ollama returned empty response")
                return ""

            logger.info(f"✅ Generated response: {len(generated_text)} chars")
            return generated_text

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise LLMConnectionError(
                f"Не удалось подключиться к Ollama по адресу {self.base_url}. "
                "Убедитесь, что сервис запущен."
            ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama request timeout: {e}")
            raise LLMTimeoutError("Превышено время ожидания ответа от Ollama.") from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise LLMGenerationError(f"Ошибка HTTP при обращении к Ollama: {e}") from e

        except LLMGenerationError:
            # Пробрасываем LLMGenerationError без изменений (включая HTTP 500)
            raise

        except Exception as e:
            logger.error(f"Unexpected error during Ollama generation: {e}")
            raise LLMGenerationError(f"Неожиданная ошибка при генерации: {e}") from e
