import pytest

from app.exceptions.providers import LLMProviderError
from app.services.rag_service import RAGService


class DummyStorage:
    def get_file(self, object_name):
        return b"sample text"


class DummyExtractor:
    def extract(self, file_data, filename):
        return "Alpha beta gamma.\nDelta epsilon zeta."


class DummyEmbedding:
    def embed_documents(self, texts):
        return [[0.1, 0.2] for _ in texts]

    def embed_query(self, text):
        return [0.3, 0.4]


class DummyVectorStore:
    def add_documents(self, texts, embeddings, ids, metadatas=None):
        self.added = {"texts": texts, "ids": ids, "metadatas": metadatas}

    def query(self, embedding, limit=5):
        return [{"text": "doc chunk", "score": 0.98, "metadata": {"document_id": "doc"}}]


class DummyLLM:
    def generate(self, prompt, max_tokens=512):
        return "generated answer"


def test_process_document_indexes_chunks_and_metadata():
    vector_store = DummyVectorStore()
    service = RAGService(
        storage=DummyStorage(),
        extractor=DummyExtractor(),
        embedding=DummyEmbedding(),
        vector_store=vector_store,
    )

    service.process_document(
        object_name="report.pdf",
        document_id="postgres-document-id",
    )

    assert vector_store.added["texts"]
    assert vector_store.added["ids"][0] == "postgres-document-id_chunk_0"
    assert vector_store.added["metadatas"][0]["document_id"] == "postgres-document-id"
    assert vector_store.added["metadatas"][0]["object_name"] == "report.pdf"
    assert vector_store.added["metadatas"][0]["chunk_index"] == 0


def test_search_uses_embedding_and_vector_store():
    vector_store = DummyVectorStore()
    service = RAGService(
        storage=DummyStorage(),
        extractor=DummyExtractor(),
        embedding=DummyEmbedding(),
        vector_store=vector_store,
    )

    results = service.search("question")

    assert results[0]["text"] == "doc chunk"


def test_answer_raises_when_llm_missing():
    service = RAGService(
        storage=DummyStorage(),
        extractor=DummyExtractor(),
        embedding=DummyEmbedding(),
        vector_store=DummyVectorStore(),
    )

    with pytest.raises(LLMProviderError):
        service.answer("What is this?")


def test_answer_returns_llm_response_when_providers_available():
    service = RAGService(
        storage=DummyStorage(),
        extractor=DummyExtractor(),
        embedding=DummyEmbedding(),
        vector_store=DummyVectorStore(),
        llm=DummyLLM(),
    )

    answer = service.answer("What is this?")

    assert answer == "generated answer"


def test_split_text_creates_chunks_from_new_lines():
    service = RAGService(
        storage=DummyStorage(),
        extractor=DummyExtractor(),
        embedding=DummyEmbedding(),
        vector_store=DummyVectorStore(),
    )

    chunks = service._split_text("one\ntwo\nthree")

    assert len(chunks) == 1
    assert chunks[0].startswith("one")
