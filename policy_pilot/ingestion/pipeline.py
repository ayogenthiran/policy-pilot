"""Ingest PDFs into a Weaviate chunk collection with OpenAI vectors."""

from __future__ import annotations

from pathlib import Path

from weaviate.classes.data import DataObject

from policy_pilot.config import get_settings
from policy_pilot.ingestion.chunking import chunk_pages
from policy_pilot.ingestion.embeddings import embed_texts
from policy_pilot.ingestion.pdf import load_pdf_pages
from policy_pilot.vectordb import (
    connect_weaviate,
    create_chunk_collection,
    library_class_name,
)


def ingest_pdf(
    pdf_path: Path,
    *,
    collection_slug: str | None = None,
    recreate_collection: bool = False,
    batch_size: int = 64,
) -> int:
    """
    Chunk a PDF, embed with OpenAI, upsert into Weaviate.

    Returns number of objects inserted.
    """
    s = get_settings()
    slug = collection_slug or s.collection_slug
    class_name = library_class_name(slug)
    path = pdf_path.resolve()

    pages = load_pdf_pages(path)
    if not pages:
        raise ValueError(f"No extractable text in {path}")

    rows = chunk_pages(pages, s)
    if not rows:
        raise ValueError(f"No chunks produced from {path}")

    texts = [t for _, _, t in rows]

    client = connect_weaviate()
    try:
        if recreate_collection:
            if client.collections.exists(class_name):
                client.collections.delete(class_name)
        if not client.collections.exists(class_name):
            create_chunk_collection(client, class_name)

        collection = client.collections.get(class_name)
        inserted = 0
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start : start + batch_size]
            batch_rows = rows[start : start + batch_size]
            vectors = embed_texts(batch_texts)
            objects: list[DataObject] = []
            for (page_num, chunk_index, text), vec in zip(batch_rows, vectors, strict=True):
                objects.append(
                    DataObject(
                        properties={
                            "text": text,
                            "source_file": str(path),
                            "file_name": path.name,
                            "page": page_num,
                            "chunk_index": chunk_index,
                            "source": "pdf",
                        },
                        vector=vec,
                    )
                )
            collection.data.insert_many(objects)
            inserted += len(objects)
        return inserted
    finally:
        client.close()
