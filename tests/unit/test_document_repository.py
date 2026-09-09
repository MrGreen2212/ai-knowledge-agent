from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.repositories.document_repository import DocumentRepository


def make_db(document):
    query = Mock()
    query.filter.return_value.first.return_value = document
    db = Mock()
    db.query.return_value = query
    return db


def test_delete_existing_document_commits_and_returns_true():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id)
    db = make_db(document)

    assert DocumentRepository().delete(db=db, document_id=document_id) is True

    db.delete.assert_called_once_with(document)
    db.commit.assert_called_once_with()


def test_delete_missing_document_returns_false_without_delete_or_commit():
    document_id = uuid4()
    db = make_db(None)

    assert DocumentRepository().delete(db=db, document_id=document_id) is False

    db.delete.assert_not_called()
    db.commit.assert_not_called()
