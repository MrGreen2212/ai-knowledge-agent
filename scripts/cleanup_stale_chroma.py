"""Удаляет stale chunks в Chroma относительно PostgreSQL."""

from collections import defaultdict
from typing import Any

from app.core.database import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.services.providers.chroma_provider import ChromaProvider


def main() -> None:
    db = SessionLocal()
    try:
        documents = DocumentRepository().list(db=db, limit=100, offset=0)
        postgres_document_ids = {str(document.id) for document in documents}
    finally:
        db.close()

    provider = ChromaProvider()
    raw = provider.collection.get(include=["metadatas"])
    chunk_ids = raw.get("ids") or []
    metadatas = raw.get("metadatas") or []

    chunks_by_document: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk_id, metadata in zip(chunk_ids, metadatas):
        metadata = metadata or {}
        document_id = str(metadata.get("document_id"))
        chunks_by_document[document_id].append(
            {
                "id": chunk_id,
                "object_name": metadata.get("object_name"),
                "chunk_index": metadata.get("chunk_index"),
            }
        )

    stale_document_ids = sorted(
        document_id
        for document_id in chunks_by_document
        if document_id not in postgres_document_ids
    )
    stale_chunk_ids = [
        chunk["id"]
        for document_id in stale_document_ids
        for chunk in chunks_by_document[document_id]
    ]

    print("STALE CHROMA CLEANUP")
    print("=" * 80)
    print(f"stale document count: {len(stale_document_ids)}")
    print(f"stale chunk count: {len(stale_chunk_ids)}")
    print("stale document_id:")
    for document_id in stale_document_ids:
        print(f"  {document_id}")

    provider.delete_documents(stale_chunk_ids)

    final_total_chunks = provider.count()
    final_raw = provider.collection.get(include=["metadatas"])
    final_ids = final_raw.get("ids") or []
    final_metadatas = final_raw.get("metadatas") or []
    final_chunks_by_document: defaultdict[str, int] = defaultdict(int)

    for metadata in final_metadatas:
        document_id = str((metadata or {}).get("document_id"))
        final_chunks_by_document[document_id] += 1

    print("=" * 80)
    print("FINAL CHROMA STATE")
    print(f"total chunks: {final_total_chunks}")
    print(f"unique document count: {len(final_chunks_by_document)}")
    print("chunks by document_id:")
    for document_id, chunk_count in sorted(final_chunks_by_document.items()):
        print(f"  {document_id}: {chunk_count}")
    print(f"metadata records checked: {len(final_ids)}")


if __name__ == "__main__":
    main()
