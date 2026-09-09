"""Read-only диагностика рассинхронизации PostgreSQL documents и Chroma chunks."""

import json
from collections import defaultdict
from typing import Any

from app.core.database import SessionLocal
from app.models.document import Document
from app.services.providers.chroma_provider import ChromaProvider


def main() -> None:
    db = SessionLocal()
    try:
        postgres_documents = db.query(Document).all()
        postgres_document_ids = {str(document.id) for document in postgres_documents}

        chroma = ChromaProvider()
        chroma_chunk_count = chroma.count()
        chroma_metadata = chroma.get_all_chunk_metadata()

        chunks_by_document: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "first_chunk_index": None,
                "last_chunk_index": None,
                "object_names": set(),
            }
        )

        for metadata in chroma_metadata:
            document_id = str(metadata.get("document_id"))
            summary = chunks_by_document[document_id]
            chunk_index = metadata.get("chunk_index")
            summary["count"] += 1
            summary["object_names"].add(str(metadata.get("object_name")))

            if isinstance(chunk_index, int):
                first_index = summary["first_chunk_index"]
                last_index = summary["last_chunk_index"]
                summary["first_chunk_index"] = (
                    chunk_index if first_index is None else min(first_index, chunk_index)
                )
                summary["last_chunk_index"] = (
                    chunk_index if last_index is None else max(last_index, chunk_index)
                )

        chroma_document_ids = set(chunks_by_document)
        report = {
            "postgres": {
                "document_count": len(postgres_documents),
                "document_ids": sorted(postgres_document_ids),
                "documents": [
                    {
                        "id": str(document.id),
                        "object_name": document.object_name,
                        "filename": document.filename,
                    }
                    for document in postgres_documents
                ],
            },
            "chroma": {
                "chunk_count": chroma_chunk_count,
                "document_count": len(chroma_document_ids),
                "chunks_by_document_id": {
                    document_id: {
                        **summary,
                        "object_names": sorted(summary["object_names"]),
                    }
                    for document_id, summary in sorted(chunks_by_document.items())
                },
            },
            "mismatches": {
                "postgres_document_ids_missing_in_chroma": sorted(
                    postgres_document_ids - chroma_document_ids
                ),
                "chroma_document_ids_missing_in_postgres": sorted(
                    chroma_document_ids - postgres_document_ids
                ),
            },
        }

        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
