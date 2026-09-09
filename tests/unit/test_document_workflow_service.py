from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

import pytest

from app.exceptions.providers import StorageDeleteError
from app.services.document_workflow_service import DocumentWorkflowService


def make_workflow(document, chunk_ids=None):
    calls = []
    document_service = Mock()
    document_service.get_document.side_effect = lambda db, document_id: (
        calls.append(("document_get", document_id)) or document
    )
    document_service.storage.delete_file.side_effect = lambda object_name: calls.append(
        ("storage_delete", object_name)
    )
    document_service.repository.delete.side_effect = lambda db, document_id: (
        calls.append(("repository_delete", document_id)) or True
    )

    chroma_provider = Mock()
    chroma_provider.get_chunk_ids_by_document_id.side_effect = (
        lambda document_id: calls.append(("chroma_get", document_id)) or (chunk_ids or [])
    )
    chroma_provider.delete_documents.side_effect = lambda ids: calls.append(
        ("chroma_delete", ids)
    )

    workflow = DocumentWorkflowService(
        document_service=document_service,
        rag_service=Mock(),
        chroma_provider=chroma_provider,
    )
    return workflow, document_service, chroma_provider, calls


def test_delete_document_removes_only_document_chunks_in_order():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    chunk_ids = [
        "document-id_chunk_0",
        "document-id_chunk_1",
        "document-id_chunk_2",
    ]
    workflow, document_service, chroma_provider, calls = make_workflow(
        document,
        chunk_ids,
    )

    assert workflow.delete_document(db=object(), document_id=document_id) is True

    assert calls == [
        ("document_get", document_id),
        ("chroma_get", document_id),
        ("chroma_delete", chunk_ids),
        ("storage_delete", "document.pdf"),
        ("repository_delete", document_id),
    ]
    chroma_provider.delete_documents.assert_called_once_with(chunk_ids)
    document_service.storage.delete_file.assert_called_once_with("document.pdf")
    document_service.repository.delete.assert_called_once()


def test_delete_document_returns_false_when_document_is_missing():
    workflow, document_service, chroma_provider, _ = make_workflow(None)
    document_service.get_document.return_value = None
    document_id = uuid4()

    assert workflow.delete_document(db=object(), document_id=document_id) is False

    chroma_provider.get_chunk_ids_by_document_id.assert_not_called()
    chroma_provider.delete_documents.assert_not_called()
    document_service.storage.delete_file.assert_not_called()
    document_service.repository.delete.assert_not_called()


def test_delete_document_continues_when_document_has_no_chunks():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    workflow, document_service, chroma_provider, calls = make_workflow(document, [])

    assert workflow.delete_document(db=object(), document_id=document_id) is True

    chroma_provider.delete_documents.assert_called_once_with([])
    assert calls[-2:] == [
        ("storage_delete", "document.pdf"),
        ("repository_delete", document_id),
    ]


def test_delete_document_does_not_continue_after_chroma_error():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    workflow, document_service, chroma_provider, _ = make_workflow(document)
    chroma_provider.get_chunk_ids_by_document_id.side_effect = RuntimeError("chroma read failed")

    with pytest.raises(RuntimeError, match="chroma read failed"):
        workflow.delete_document(db=object(), document_id=document_id)

    chroma_provider.delete_documents.assert_not_called()
    document_service.storage.delete_file.assert_not_called()
    document_service.repository.delete.assert_not_called()


def test_delete_document_does_not_continue_after_chroma_delete_error():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    workflow, document_service, chroma_provider, _ = make_workflow(
        document,
        ["document-id_chunk_0"],
    )
    chroma_provider.delete_documents.side_effect = RuntimeError("chroma delete failed")

    with pytest.raises(RuntimeError, match="chroma delete failed"):
        workflow.delete_document(db=object(), document_id=document_id)

    document_service.storage.delete_file.assert_not_called()
    document_service.repository.delete.assert_not_called()


def test_delete_document_does_not_delete_postgres_after_minio_error():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    workflow, document_service, chroma_provider, _ = make_workflow(
        document,
        ["document-id_chunk_0"],
    )
    document_service.storage.delete_file.side_effect = StorageDeleteError("minio failed")

    with pytest.raises(StorageDeleteError, match="minio failed"):
        workflow.delete_document(db=object(), document_id=document_id)

    chroma_provider.delete_documents.assert_called_once_with(["document-id_chunk_0"])
    document_service.repository.delete.assert_not_called()


def test_delete_document_propagates_postgres_error():
    document_id = uuid4()
    document = SimpleNamespace(id=document_id, object_name="document.pdf")
    workflow, document_service, chroma_provider, _ = make_workflow(
        document,
        ["document-id_chunk_0"],
    )
    document_service.repository.delete.side_effect = RuntimeError("postgres failed")

    with pytest.raises(RuntimeError, match="postgres failed"):
        workflow.delete_document(db=object(), document_id=document_id)

    chroma_provider.delete_documents.assert_called_once_with(["document-id_chunk_0"])
    document_service.storage.delete_file.assert_called_once_with("document.pdf")
