import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def client():
    with TestClient(fastapi_app, lifespan="off") as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "test")
    monkeypatch.setenv("MINIO_SECRET_KEY", "test")
    monkeypatch.setenv("MINIO_BUCKET", "test-bucket")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "tiny")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
