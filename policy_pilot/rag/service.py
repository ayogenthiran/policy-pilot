"""End-to-end RAG answer from Weaviate + OpenAI chat."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from policy_pilot.config import Settings, get_settings
from policy_pilot.rag.retriever import ChunkMetadataFilter, search_chunks
from policy_pilot.vectordb import connect_weaviate, library_class_name


def _bm25_property_list(s: Settings) -> list[str]:
    props = [p.strip() for p in s.rag_hybrid_bm25_properties.split(",") if p.strip()]
    return props if props else ["text"]


def _retrieve_hits(
    s: Settings,
    question: str,
    class_name: str,
    k: int,
    metadata_filter: ChunkMetadataFilter | None = None,
) -> list[dict[str, Any]]:
    embedder = OpenAIEmbeddings(api_key=s.openai_api_key, model=s.embedding_model)
    qvec = embedder.embed_query(question)
    client = connect_weaviate()
    try:
        if not client.collections.exists(class_name):
            raise ValueError(
                f"Weaviate collection {class_name!r} does not exist. Ingest a PDF first."
            )
        return search_chunks(
            client,
            class_name,
            query_text=question,
            query_vector=qvec,
            limit=k,
            alpha=s.rag_hybrid_alpha,
            bm25_properties=_bm25_property_list(s),
            metadata_filter=metadata_filter,
        )
    finally:
        client.close()


def _context_from_hits(hits: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for i, h in enumerate(hits, start=1):
        text = h.get("text") or ""
        score = h.get("score")
        score_bit = f", score={score:.4f}" if isinstance(score, (int, float)) else ""
        meta = (
            f"(source={h.get('file_name')}, page={h.get('page')}, "
            f"chunk={h.get('chunk_index')}{score_bit})"
        )
        blocks.append(f"[{i}] {meta}\n{text}")
    return "\n\n".join(blocks) if blocks else "(no retrieved context)"


def _answer_from_context(s: Settings, question: str, context: str) -> str:
    llm = ChatOpenAI(
        api_key=s.openai_api_key,
        model=s.chat_model,
        temperature=0.2,
    )
    system = (
        "You are a careful policy assistant. Answer using only the provided context. "
        "If the context is insufficient, say so. Cite snippet numbers [1], [2] when relevant."
    )
    user = f"Context:\n{context}\n\nQuestion: {question}"
    msg = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
    )
    return msg.content if isinstance(msg.content, str) else str(msg.content)


def query_rag(
    question: str,
    *,
    collection_slug: str | None = None,
    weaviate_class_name: str | None = None,
    top_k: int | None = None,
    metadata_filter: ChunkMetadataFilter | None = None,
) -> dict[str, Any]:
    """
    Embed the question, retrieve chunks, call the chat model with context.

    Use ``weaviate_class_name`` to query an existing Weaviate collection by exact name
    (for data already in the vector DB). Otherwise ``collection_slug`` is mapped with
    ``library_class_name`` (same as ingest).

    Returns ``{"answer": str, "sources": list[dict]}``.
    """
    s = get_settings()
    if not s.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    direct = (weaviate_class_name or "").strip()
    if direct:
        class_name = direct
    else:
        slug = collection_slug or s.collection_slug
        class_name = library_class_name(slug)
    k = top_k if top_k is not None else s.rag_top_k

    hits = _retrieve_hits(s, question, class_name, k, metadata_filter)
    context = _context_from_hits(hits)
    answer = _answer_from_context(s, question, context)
    return {"answer": answer, "sources": hits}
