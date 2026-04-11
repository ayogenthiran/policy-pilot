"""Simple Streamlit UI for Policy Pilot RAG (in-process; use FastAPI for remote clients)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from policy_pilot.config import get_settings
from policy_pilot.knowledge_base import list_knowledge_bases
from policy_pilot.rag.retriever import ChunkMetadataFilter
from policy_pilot.rag.service import query_rag
from policy_pilot.vectordb import library_class_name

st.set_page_config(page_title="Policy Pilot", layout="wide")


@st.cache_data(ttl=30)
def _cached_kb_names() -> list[str]:
    try:
        return list_knowledge_bases()
    except Exception:
        return []


def _render_sidebar() -> tuple[str | None, str, int, ChunkMetadataFilter | None]:
    s = get_settings()
    st.sidebar.subheader("Knowledge base")
    names = _cached_kb_names()
    default_class = library_class_name(s.collection_slug)
    opts = ["(use slug below)"] + sorted(names)
    default_index = opts.index(default_class) if default_class in names else 0
    kb_choice = st.sidebar.selectbox(
        "Weaviate collection",
        opts,
        index=min(default_index, len(opts) - 1),
        help="Chunked vectors already in Weaviate are queried as-is; pick a collection or use a slug.",
    )
    weaviate_class = None if kb_choice == "(use slug below)" else kb_choice

    st.sidebar.caption("Settings")
    slug = st.sidebar.text_input("Collection slug (when using slug)", value=s.collection_slug)
    top_k = st.sidebar.number_input(
        "Chunks to retrieve", min_value=1, max_value=30, value=s.rag_top_k
    )
    st.sidebar.caption("Optional: restrict retrieval to one PDF (exact file name).")
    only_file = st.sidebar.text_input("Filter by file name", value="").strip()
    meta: ChunkMetadataFilter | None = (
        ChunkMetadataFilter(file_name=only_file) if only_file else None
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        "**Ingest (CLI)**  \n"
        "`python scripts/ingest.py data/your.pdf`  \n"
        "`--recreate` to replace the collection"
    )
    data_dir = Path("data")
    if data_dir.is_dir():
        pdfs = sorted(data_dir.glob("*.pdf"))
        if pdfs:
            st.sidebar.caption("PDFs in `data/`:")
            for p in pdfs:
                st.sidebar.text(p.name)
    return (
        weaviate_class,
        slug.strip() or s.collection_slug,
        int(top_k),
        meta,
    )


def _render_sources(sources: list[dict[str, Any]]) -> None:
    with st.expander("Sources"):
        for i, src in enumerate(sources, start=1):
            score = src.get("score")
            score_s = f" · hybrid score {score:.4f}" if isinstance(score, (int, float)) else ""
            st.markdown(
                f"**[{i}]** `{src.get('file_name')}` p.{src.get('page')} "
                f"· chunk {src.get('chunk_index')}{score_s}"
            )
            body = src.get("text") or ""
            clipped = body[:800] + ("…" if len(body) > 800 else "")
            st.text(clipped)


def _run_turn(
    question: str,
    weaviate_class: str | None,
    slug: str,
    top_k: int,
    metadata_filter: ChunkMetadataFilter | None,
) -> None:
    st.session_state.messages.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving and generating…"):
                out = query_rag(
                    question,
                    collection_slug=slug or None,
                    weaviate_class_name=weaviate_class,
                    top_k=top_k,
                    metadata_filter=metadata_filter,
                )
            st.markdown(out["answer"])
            _render_sources(out["sources"])
            st.session_state.messages.append(("assistant", out["answer"]))
        except Exception as exc:
            err = f"**Error.** {exc}"
            st.error(str(exc))
            st.session_state.messages.append(("assistant", err))


def main() -> None:
    st.title("Policy Pilot")
    st.caption("Knowledge base = Weaviate chunk collections · OpenAI embeddings + chat")

    weaviate_class, slug, top_k, metadata_filter = _render_sidebar()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for role, content in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(content)

    question = st.chat_input("Ask about your policy documents…")
    if question:
        _run_turn(question, weaviate_class, slug, top_k, metadata_filter)


# Streamlit runs this file in a synthetic __main__ module; do not gate on __name__.
main()
