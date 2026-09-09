from unittest.mock import Mock

import pytest
from minio.error import S3Error

from app.exceptions.providers import StorageDeleteError
from app.services.providers.minio_provider import MinIOProvider


def test_delete_file_removes_object_from_configured_bucket():
    provider = object.__new__(MinIOProvider)
    provider.client = Mock()
    provider.bucket_name = "test-bucket"

    provider.delete_file("document.pdf")

    provider.client.remove_object.assert_called_once_with(
        bucket_name="test-bucket",
        object_name="document.pdf",
    )


def test_delete_file_wraps_s3_error():
    provider = object.__new__(MinIOProvider)
    provider.client = Mock()
    provider.bucket_name = "test-bucket"
    response = Mock()
    provider.client.remove_object.side_effect = S3Error(
        "InternalError",
        "delete failed",
        "document.pdf",
        "request-id",
        "host-id",
        response,
    )

    with pytest.raises(StorageDeleteError, match="document.pdf"):
        provider.delete_file("document.pdf")
