"""Token-sized recursive splits for embedding models."""

from __future__ import annotations

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from policy_pilot.config import Settings


def _encoding_for_embedding(model: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(model)
    except (KeyError, ValueError):
        return tiktoken.get_encoding("cl100k_base")


def chunk_pages(
    pages: list[tuple[int, str]],
    settings: Settings,
) -> list[tuple[int, int, str]]:
    """Split pages into (page_number, chunk_index, text). Chunk index is per document, stable order."""
    enc = _encoding_for_embedding(settings.embedding_model)

    def length_fn(s: str) -> int:
        return len(enc.encode(s))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size_tokens,
        chunk_overlap=settings.chunk_overlap_tokens,
        length_function=length_fn,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    out: list[tuple[int, int, str]] = []
    i = 0
    for page_num, text in pages:
        for piece in splitter.split_text(text):
            piece = piece.strip()
            if piece:
                out.append((page_num, i, piece))
                i += 1
    return out
