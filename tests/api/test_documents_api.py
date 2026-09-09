from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import documents as documents_api
from app.main import app


class DummyWorkflow:
    def upload_document(self, db, file_data, filename, content_type):
        return {
            "id": "doc-1",
            "filename": filename,
            "status": "uploaded",
            "object_name": "stored.bin",
            "size": len(file_data),
        }

    def delete_document(self, db, document_id):
        return True


def test_upload_document_returns_created_status(monkeypatch):
    app.dependency_overrides[documents_api.get_document_workflow_service] = lambda: DummyWorkflow()

    with TestClient(app) as client:
        response = client.post(
            "/documents/upload",
            files={"file": ("sample.txt", b"hello", "text/plain")},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"
    assert response.json()["filename"] == "sample.txt"


def test_delete_document_returns_no_content():
    document_id = uuid4()
    workflow = DummyWorkflow()
    app.dependency_overrides[documents_api.get_document_workflow_service] = lambda: workflow

    try:
        with TestClient(app) as client:
            response = client.delete(f"/documents/{document_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204


def test_delete_missing_document_returns_not_found():
    class MissingWorkflow(DummyWorkflow):
        def delete_document(self, db, document_id):
            return False

    app.dependency_overrides[documents_api.get_document_workflow_service] = MissingWorkflow

    try:
        with TestClient(app) as client:
            response = client.delete(f"/documents/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_delete_workflow_error_is_not_returned_as_success():
    class FailingWorkflow(DummyWorkflow):
        def delete_document(self, db, document_id):
            raise RuntimeError("delete failed")

    app.dependency_overrides[documents_api.get_document_workflow_service] = FailingWorkflow

    try:
        with pytest.raises(RuntimeError, match="delete failed"):
            with TestClient(app) as client:
                client.delete(f"/documents/{uuid4()}")
    finally:
        app.dependency_overrides.clear()
