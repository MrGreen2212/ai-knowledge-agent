from types import SimpleNamespace

from app.services.document_service import DocumentService


class DummyStorage:
    def upload_file(self, file_data, original_filename, content_type):
        return {
            "status": "success",
            "bucket": "test-bucket",
            "object_name": "abc123.txt",
            "original_filename": original_filename,
            "size": len(file_data),
        }


class DummyRepository:
    def create(self, db, filename, object_name, content_type, size):
        return SimpleNamespace(
            id="doc-1",
            filename=filename,
            object_name=object_name,
            content_type=content_type,
            size=size,
        )


def test_create_document_persists_metadata_and_returns_summary():
    service = DocumentService(repository=DummyRepository(), storage=DummyStorage())

    result = service.create_document(
        db=object(),
        file_data=b"hello world",
        filename="notes.txt",
        content_type="text/plain",
    )

    assert result["id"] == "doc-1"
    assert result["filename"] == "notes.txt"
    assert result["object_name"] == "abc123.txt"
    assert result["status"] == "uploaded"
    assert result["size"] == 11
