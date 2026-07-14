from typing import List
# Исправление импорта под новую версию FastEmbed >= 0.4.3
from fastembed import TextEmbedding as TextEmbeddingModel


class EmbeddingService:
    """Сервис для превращения текста в числовые векторы."""

    def __init__(self):
        # Проверку наличия ONNX оставляем здесь
        try:
            self.model = TextEmbeddingModel(  # <-- Используем новое название
                name="sentence-transformers/all-MiniLM-L6-v2",  # Без resolve_
                device="cpu",
            )
        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить модель эмбеддингов: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        embedding = next(self.model.embed([text]))
        return embedding.tolist()