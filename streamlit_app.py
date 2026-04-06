"""Simple Streamlit UI for Policy Pilot RAG (in-process; use FastAPI for remote clients)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from policy_pilot.config import get_settings
from policy_pilot.rag.service import query_rag

st.set_page_config(page_title="Policy Pilot", layout="wide")


def _render_sidebar() -> tuple[str, int]:
    s = get_settings()
    st.sidebar.subheader("Settings")
    slug = st.sidebar.text_input("Collection slug", value=s.collection_slug)
    top_k = st.sidebar.number_input(
        "Chunks to retrieve", min_value=1, max_value=30, value=s.rag_top_k
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
    return slug.strip() or s.collection_slug, int(top_k)


def _render_sources(sources: list[dict[str, Any]]) -> None:
    with st.expander("Sources"):
        for i, src in enumerate(sources, start=1):
            st.markdown(f"**[{i}]** `{src.get('file_name')}` p.{src.get('page')}")
            body = src.get("text") or ""
            clipped = body[:800] + ("…" if len(body) > 800 else "")
            st.text(clipped)


def _run_turn(question: str, slug: str, top_k: int) -> None:
    st.session_state.messages.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving and generating…"):
                out = query_rag(
                    question,
                    collection_slug=slug or None,
                    top_k=top_k,
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
    st.caption("RAG over PDFs in Weaviate · OpenAI embeddings + chat")

    slug, top_k = _render_sidebar()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for role, content in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(content)

    question = st.chat_input("Ask about your policy documents…")
    if question:
        _run_turn(question, slug, top_k)


# Streamlit runs this file in a synthetic __main__ module; do not gate on __name__.
main()
