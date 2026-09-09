from types import SimpleNamespace

from app.services.document_service import DocumentService
from app.services.document_workflow_service import DocumentWorkflowService
from app.services.rag_service import RAGService


class FakeStorage:
    def __init__(self):
        self.files = {"doc-1": b"Alpha beta gamma"}

    def get_file(self, object_name):
        return self.files[object_name]

    def upload_file(self, file_data, original_filename, content_type):
        object_name = "doc-1"
        self.files[object_name] = file_data
        return {
            "status": "success",
            "bucket": "test-bucket",
            "object_name": object_name,
            "original_filename": original_filename,
            "size": len(file_data),
        }


class FakeExtractor:
    def extract(self, file_data, filename):
        return "Alpha beta gamma. Delta epsilon zeta."


class FakeEmbedding:
    def embed_documents(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [0.5, 0.5]


class FakeVectorStore:
    def __init__(self):
        self.documents = []

    def add_documents(self, texts, embeddings, ids, metadatas=None):
        self.documents.extend(zip(texts, ids, metadatas or []))

    def query(self, embedding, limit=5):
        return [{"text": "Alpha beta gamma.", "score": 0.99, "metadata": {"document_id": "doc"}}]


class FakeLLM:
    def generate(self, prompt, max_tokens=512):
        return "answer from fake llm"


class FakeRepository:
    def create(self, db, filename, object_name, content_type, size):
        return SimpleNamespace(
            id="doc-1",
            filename=filename,
            object_name=object_name,
            content_type=content_type,
            size=size,
        )


def test_full_rag_pipeline_runs_with_fakes():
    storage = FakeStorage()
    extractor = FakeExtractor()
    embedding = FakeEmbedding()
    vector_store = FakeVectorStore()
    llm = FakeLLM()

    document_service = DocumentService(repository=FakeRepository(), storage=storage)
    rag_service = RAGService(
        storage=storage,
        extractor=extractor,
        embedding=embedding,
        vector_store=vector_store,
        llm=llm,
    )
    workflow = DocumentWorkflowService(document_service=document_service, rag_service=rag_service)

    document = workflow.upload_document(
        db=object(),
        file_data=b"Alpha beta gamma",
        filename="sample.txt",
        content_type="text/plain",
    )

    results = rag_service.search("gamma")
    answer = rag_service.answer("What is this?", top_k=1)

    assert document["status"] == "uploaded"
    assert document["object_name"] == "doc-1"
    assert results[0]["text"] == "Alpha beta gamma."
    assert answer == "answer from fake llm"
    assert vector_store.documents
