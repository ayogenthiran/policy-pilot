"""Hybrid retrieval: BM25 + HNSW vector search with optional metadata filters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import weaviate
from weaviate.classes.query import Filter, MetadataQuery

PROP_NAMES = ["text", "source_file", "file_name", "page", "chunk_index", "source"]


@dataclass
class ChunkMetadataFilter:
    """Optional filters on stored chunk metadata (Weaviate ``where`` clause)."""

    file_name: str | None = None
    source_file: str | None = None
    source: str | None = None
    page_min: int | None = None
    page_max: int | None = None


def _weaviate_filter(meta: ChunkMetadataFilter | None) -> Any | None:
    if meta is None:
        return None
    parts: list[Any] = []
    if meta.file_name is not None:
        parts.append(Filter.by_property("file_name").equal(meta.file_name))
    if meta.source_file is not None:
        parts.append(Filter.by_property("source_file").equal(meta.source_file))
    if meta.source is not None:
        parts.append(Filter.by_property("source").equal(meta.source))
    if meta.page_min is not None:
        parts.append(Filter.by_property("page").greater_or_equal(meta.page_min))
    if meta.page_max is not None:
        parts.append(Filter.by_property("page").less_or_equal(meta.page_max))
    if not parts:
        return None
    out: Any = parts[0]
    for p in parts[1:]:
        out = out & p
    return out


def search_chunks(
    client: weaviate.WeaviateClient,
    class_name: str,
    *,
    query_text: str,
    query_vector: list[float],
    limit: int,
    alpha: float = 0.75,
    bm25_properties: list[str] | None = None,
    metadata_filter: ChunkMetadataFilter | None = None,
    return_scores: bool = True,
) -> list[dict[str, Any]]:
    """
    Hybrid search: BM25 over ``bm25_properties`` plus ANN over the HNSW vector index.

    The query text drives keyword relevance; ``query_vector`` drives semantic neighbors.
    """
    collection = client.collections.get(class_name)
    qp = (
        bm25_properties
        if bm25_properties
        else ["text"]
    )
    filters = _weaviate_filter(metadata_filter)
    meta = MetadataQuery(score=True, distance=True) if return_scores else None

    response = collection.query.hybrid(
        query=query_text,
        vector=query_vector,
        alpha=alpha,
        query_properties=qp,
        limit=limit,
        filters=filters,
        return_properties=PROP_NAMES,
        return_metadata=meta,
    )

    hits: list[dict[str, Any]] = []
    for obj in response.objects:
        props = obj.properties or {}
        row: dict[str, Any] = {k: props.get(k) for k in PROP_NAMES}
        if return_scores and obj.metadata is not None:
            row["score"] = obj.metadata.score
            row["distance"] = obj.metadata.distance
        hits.append(row)
    return hits
