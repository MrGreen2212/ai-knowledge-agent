import logging
from typing import Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Сервис для взаимодействия с Ollama через HTTP API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"OllamaService initialized with URL: {self.base_url}, Model: {self.model}")

    def generate(self, prompt: str) -> str:
        """
        Отправляет запрос в Ollama и возвращает сгенерированный текст.

        Args:
            prompt: Текст запроса для генерации ответа.

        Returns:
            Сгенерированный текст ответа от модели.

        Raises:
            ConnectionError: Если не удалось подключиться к Ollama.
            RuntimeError: Если произошла ошибка при генерации.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            logger.debug(f"Sending request to Ollama: {url}")
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "")

            if not generated_text:
                logger.warning("Ollama returned empty response")
                return ""

            logger.info(f"Generated response length: {len(generated_text)} characters")
            return generated_text

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise ConnectionError(
                f"Не удалось подключиться к Ollama по адресу {self.base_url}. "
                "Убедитесь, что сервис запущен."
            ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama request timeout: {e}")
            raise RuntimeError("Превышено время ожидания ответа от Ollama.") from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise RuntimeError(f"Ошибка HTTP при обращении к Ollama: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during Ollama generation: {e}")
            raise RuntimeError(f"Неожиданная ошибка при генерации: {e}") from e
