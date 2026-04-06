"""End-to-end RAG answer from Weaviate + OpenAI chat."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from policy_pilot.config import Settings, get_settings
from policy_pilot.rag.retriever import search_chunks
from policy_pilot.vectordb import connect_weaviate, library_class_name


def _retrieve_hits(
    s: Settings,
    question: str,
    class_name: str,
    k: int,
) -> list[dict[str, Any]]:
    embedder = OpenAIEmbeddings(api_key=s.openai_api_key, model=s.embedding_model)
    qvec = embedder.embed_query(question)
    client = connect_weaviate()
    try:
        if not client.collections.exists(class_name):
            raise ValueError(
                f"Weaviate collection {class_name!r} does not exist. Ingest a PDF first."
            )
        return search_chunks(client, class_name, qvec, limit=k)
    finally:
        client.close()


def _context_from_hits(hits: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for i, h in enumerate(hits, start=1):
        text = h.get("text") or ""
        meta = f"(source={h.get('file_name')}, page={h.get('page')})"
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
    top_k: int | None = None,
) -> dict[str, Any]:
    """
    Embed the question, retrieve chunks, call the chat model with context.

    Returns ``{"answer": str, "sources": list[dict]}``.
    """
    s = get_settings()
    if not s.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    slug = collection_slug or s.collection_slug
    class_name = library_class_name(slug)
    k = top_k if top_k is not None else s.rag_top_k

    hits = _retrieve_hits(s, question, class_name, k)
    context = _context_from_hits(hits)
    answer = _answer_from_context(s, question, context)
    return {"answer": answer, "sources": hits}
