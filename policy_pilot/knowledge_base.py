"""Knowledge bases are Weaviate collections of chunked text + embeddings."""

from __future__ import annotations

from policy_pilot.vectordb import connect_weaviate, list_collection_names


def list_knowledge_bases() -> list[str]:
    """
    Return collection names in Weaviate that can back RAG.

    Ingest writes here via ``ingest_pdf`` (class name from ``library_class_name``).
    Any collection with the same chunk properties can be queried.
    """
    client = connect_weaviate()
    try:
        return list_collection_names(client)
    finally:
        client.close()
