import pytest

from app.exceptions.providers import (
    EmbeddingGenerationError,
    LLMGenerationError,
    StorageUploadError,
    VectorStoreInsertError,
)
from app.services.providers import (
    EmbeddingProvider,
    LLMProvider,
    StorageProvider,
    VectorStoreProvider,
)


class FakeLLM(LLMProvider):
    def generate(self, prompt, max_tokens=512):
        if not prompt:
            raise LLMGenerationError("empty")
        return "ok"


class FakeEmbedding(EmbeddingProvider):
    def embed_documents(self, texts):
        if not texts:
            raise EmbeddingGenerationError("empty")
        return [[0.1, 0.2] for _ in texts]

    def embed_query(self, text):
        if not text:
            raise EmbeddingGenerationError("empty")
        return [0.1, 0.2]


class FakeVectorStore(VectorStoreProvider):
    def add_documents(self, texts, embeddings, ids, metadatas=None):
        if not texts:
            raise VectorStoreInsertError("empty")

    def query(self, embedding, limit=5):
        return []

    def lexical_search(self, query, limit=5):
        return []


class FakeStorage(StorageProvider):
    def upload_file(self, file_data, original_filename, content_type):
        if not file_data:
            raise StorageUploadError("empty")
        return {"status": "success", "object_name": original_filename}

    def get_file(self, object_name):
        return b"data"


def test_provider_interfaces_support_success_and_error_paths():
    llm = FakeLLM()
    embedding = FakeEmbedding()
    vector_store = FakeVectorStore()
    storage = FakeStorage()

    assert llm.generate("hello") == "ok"
    assert embedding.embed_documents(["a"])[0][0] == 0.1
    assert embedding.embed_query("a") == [0.1, 0.2]
    vector_store.add_documents(["a"], [[0.1]], ["1"])
    assert storage.upload_file(b"x", "file.txt", "text/plain")["status"] == "success"

    with pytest.raises(LLMGenerationError):
        llm.generate("")

    with pytest.raises(EmbeddingGenerationError):
        embedding.embed_documents([])

    with pytest.raises(VectorStoreInsertError):
        vector_store.add_documents([], [], [])

    with pytest.raises(StorageUploadError):
        storage.upload_file(b"", "file.txt", "text/plain")
