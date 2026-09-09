from fastapi.testclient import TestClient

from app.core import dependencies as dependencies_module
from app.main import app


class DummyConversationService:
    def list_conversations(self, db, limit=100, offset=0):
        return []

    def get_conversation(self, db, conversation_id):
        return None

    def get_messages(self, db, conversation_id, limit=100, offset=0):
        return []

    def delete_conversation(self, db, conversation_id):
        return False


class DummyRAGService:
    def chat(self, *args, **kwargs):
        return {"conversation_id": "conv-1", "response": "ok"}


def test_list_conversations_returns_empty_list(monkeypatch):
    monkeypatch.setattr(
        dependencies_module, "get_conversation_service", lambda: DummyConversationService()
    )
    monkeypatch.setattr(dependencies_module, "get_rag_service", lambda: DummyRAGService())

    with TestClient(app) as client:
        response = client.get("/conversations")

    assert response.status_code == 200
    assert response.json() == []


def test_get_missing_conversation_returns_404(monkeypatch):
    monkeypatch.setattr(
        dependencies_module, "get_conversation_service", lambda: DummyConversationService()
    )
    monkeypatch.setattr(dependencies_module, "get_rag_service", lambda: DummyRAGService())

    with TestClient(app) as client:
        response = client.get("/conversations/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
