from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.conversation_service import ConversationService


class DummyConversationRepository:
    def create(self, db, title=None):
        return SimpleNamespace(id=uuid4(), title=title)

    def get_by_id(self, db, conversation_id):
        if conversation_id == "missing":
            return None
        return SimpleNamespace(id=conversation_id, title="existing")

    def list(self, db, limit=100, offset=0):
        return [SimpleNamespace(id=uuid4(), title="one")]

    def delete(self, db, conversation_id):
        return conversation_id != "missing"

    def update(self, db, conversation_id, title):
        if conversation_id == "missing":
            return None
        return SimpleNamespace(id=conversation_id, title=title)

    def touch_without_commit(self, db, conversation_id):
        return conversation_id != "missing"


class DummyMessageRepository:
    def create_without_commit(self, db, conversation_id, role, content):
        return SimpleNamespace(
            id=uuid4(), conversation_id=conversation_id, role=role, content=content
        )

    def list_by_conversation(self, db, conversation_id, limit=100, offset=0):
        return [SimpleNamespace(id=uuid4(), content="hello")]


class DummyDB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, obj):
        return None


def test_create_conversation_returns_created_conversation():
    service = ConversationService(
        conversation_repository=DummyConversationRepository(),
        message_repository=DummyMessageRepository(),
    )

    conversation = service.create_conversation(db=object(), title="new")

    assert conversation.title == "new"
    assert conversation.id is not None


def test_get_conversation_returns_none_for_missing_id():
    service = ConversationService(
        conversation_repository=DummyConversationRepository(),
        message_repository=DummyMessageRepository(),
    )

    conversation = service.get_conversation(db=object(), conversation_id="missing")

    assert conversation is None


def test_add_message_commits_and_returns_message():
    db = DummyDB()
    service = ConversationService(
        conversation_repository=DummyConversationRepository(),
        message_repository=DummyMessageRepository(),
    )

    message = service.add_message(db=db, conversation_id=uuid4(), role="user", content="hi")

    assert message.content == "hi"
    assert db.commits == 1
    assert db.rollbacks == 0


def test_add_message_rolls_back_when_conversation_missing():
    db = DummyDB()
    service = ConversationService(
        conversation_repository=DummyConversationRepository(),
        message_repository=DummyMessageRepository(),
    )

    with pytest.raises(ValueError):
        service.add_message(db=db, conversation_id="missing", role="user", content="hi")

    assert db.rollbacks >= 1


def test_rename_conversation_returns_updated_conversation():
    service = ConversationService(
        conversation_repository=DummyConversationRepository(),
        message_repository=DummyMessageRepository(),
    )

    updated = service.rename_conversation(db=object(), conversation_id=uuid4(), title="updated")

    assert updated is not None
    assert updated.title == "updated"
