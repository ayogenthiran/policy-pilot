"""Vector search against Weaviate chunk collections."""

from __future__ import annotations

from typing import Any

import weaviate

PROP_NAMES = ["text", "source_file", "file_name", "page", "chunk_index", "source"]


def search_chunks(
    client: weaviate.WeaviateClient,
    class_name: str,
    query_vector: list[float],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    collection = client.collections.get(class_name)
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=limit,
        return_properties=PROP_NAMES,
    )
    hits: list[dict[str, Any]] = []
    for obj in response.objects:
        props = obj.properties or {}
        hits.append({k: props.get(k) for k in PROP_NAMES})
    return hits
