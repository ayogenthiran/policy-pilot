"""OpenAI embeddings for ingest and retrieval."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from policy_pilot.config import get_settings


def get_embedding_model() -> OpenAIEmbeddings:
    s = get_settings()
    if not s.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set (required for embeddings).")
    return OpenAIEmbeddings(api_key=s.openai_api_key, model=s.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)
