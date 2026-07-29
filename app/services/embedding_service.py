import logging
from typing import List

from fastembed import TextEmbedding as TextEmbeddingModel

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Сервис для создания эмбеддингов текста."""

    def __init__(self):
        try:
            logger.info("Loading embedding model...")
            self.model = TextEmbeddingModel(
                name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Не удалось загрузить модель эмбеддингов: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создает эмбеддинги для списка текстов."""
        embeddings = list(self.model.embed(texts))
        logger.debug(f"Generated embeddings for {len(texts)} texts")
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Создает эмбеддинг для одного текста."""
        embedding = next(self.model.embed([text]))
        return embedding.tolist()
