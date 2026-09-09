from unittest.mock import Mock

from app.services.providers.chroma_provider import ChromaProvider


def test_delete_documents_passes_ids_to_collection_delete():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()
    ids = ["document_chunk_0", "document_chunk_1"]

    provider.delete_documents(ids)

    provider.collection.delete.assert_called_once_with(ids=ids)


def test_delete_documents_does_nothing_for_empty_ids():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()

    provider.delete_documents([])

    provider.collection.delete.assert_not_called()


def test_get_chunk_ids_by_document_id_filters_metadata_and_returns_ids():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()
    provider.collection.get.return_value = {
        "ids": ["document-id_chunk_0", "document-id_chunk_1"],
        "metadatas": [
            {"document_id": "document-id", "chunk_index": 0},
            {"document_id": "document-id", "chunk_index": 1},
        ],
    }

    result = provider.get_chunk_ids_by_document_id("document-id")

    assert result == ["document-id_chunk_0", "document-id_chunk_1"]
    provider.collection.get.assert_called_once_with(
        where={"document_id": "document-id"},
        include=["metadatas"],
    )


def test_get_chunk_ids_by_document_id_returns_empty_list():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()
    provider.collection.get.return_value = {"ids": [], "metadatas": []}

    assert provider.get_chunk_ids_by_document_id("missing-document") == []


def test_lexical_search_finds_chunk_with_prefix_matching():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()
    provider.collection.get.return_value = {
        "ids": [
            "dcee88c3-3979-497a-a6d4-5e5c2f08cc4b_chunk_28",
            "unrelated_chunk_0",
        ],
        "documents": [
            "Оркестровка и хореография Web-сервисов.",
            "Только XML-документы.",
        ],
        "metadatas": [
            {
                "document_id": "dcee88c3-3979-497a-a6d4-5e5c2f08cc4b",
                "object_name": "93cdd952-6c19-4308-8434-a959b6481c73.pdf",
                "chunk_index": 28,
            },
            {"document_id": "other", "object_name": "other.pdf", "chunk_index": 0},
        ],
    }

    results = provider.lexical_search("оркестрация хореография Web-сервисов")

    assert results[0]["id"] == "dcee88c3-3979-497a-a6d4-5e5c2f08cc4b_chunk_28"
    assert results[0]["score"] > 0
    assert results[0]["metadata"]["matched_tokens"] == [
        "оркестрация",
        "хореография",
        "web",
        "сервисов",
    ]
    assert results[0]["score"] == 1.0
    assert results[0]["metadata"]["match_count"] == 4
    assert results[0]["metadata"]["match_percentage"] == 1.0
    assert results[0]["metadata"]["token_counts"] == {
        "оркестрация": 1,
        "хореография": 1,
        "web": 1,
        "сервисов": 1,
    }
    assert "что" not in results[0]["metadata"]["token_counts"]
    assert "и" not in results[0]["metadata"]["token_counts"]
    provider.collection.get.assert_called_once_with(include=["documents", "metadatas"])


def test_lexical_search_returns_empty_result_when_no_tokens_match():
    provider = object.__new__(ChromaProvider)
    provider.collection = Mock()
    provider.collection.get.return_value = {
        "ids": ["chunk_0"],
        "documents": ["Текст без совпадений."],
        "metadatas": [{"chunk_index": 0}],
    }

    assert provider.lexical_search("оркестрация") == []
